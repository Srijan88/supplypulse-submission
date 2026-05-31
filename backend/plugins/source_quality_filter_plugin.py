from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class SourceQualityFilterPlugin:
    """
    SupplyPulse source quality filter.

    Purpose:
    - Review normalized Bright Data SERP results.
    - Separate stronger sources from weaker or noisy sources.
    - Preserve all source decisions for audit.
    - Prepare cleaner evidence packs for GEO / TRADE / ROUTE agents.

    This plugin does not call an LLM.
    It only applies transparent source-quality rules.
    """

    TRUSTED_DOMAIN_HINTS = [
        ".gov",
        ".edu",
        ".int",
        "worldbank.org",
        "wto.org",
        "oecd.org",
        "imf.org",
        "un.org",
        "europa.eu",
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "bbc.co.uk",
        "ft.com",
        "bloomberg.com",
        "channelnewsasia.com",
        "aljazeera.com",
        "lowyinstitute.org",
        "csis.org",
        "brookings.edu",
        "chathamhouse.org",
        "iiss.org",
    ]

    USABLE_DOMAIN_HINTS = [
        "asianews.network",
        "spglobal.com",
        "lloydslist.com",
        "maritime-executive.com",
        "porttechnology.org",
        "splash247.com",
        "joc.com",
        "freightwaves.com",
        "tradewindsnews.com",
        "content.ballastmarkets.com",
        "supplychaindive.com",
        "container-news.com",
        "customs.gov",
        "trade.gov",
    ]

    LOWER_QUALITY_DOMAIN_HINTS = [
        "facebook.com",
        "x.com",
        "twitter.com",
        "instagram.com",
        "tiktok.com",
        "reddit.com",
        "quora.com",
        "medium.com",
        "linkedin.com",
        "youtube.com",
        "pinterest.com",
    ]

    BLOCKED_DOMAIN_HINTS = [
        "google.com/search",
        "webcache.googleusercontent.com",
    ]

    def filter_sources(
        self,
        bright_data_result: Dict[str, Any],
        max_trusted: int = 8,
        max_usable: int = 8,
        audit_plugin: Optional[Any] = None,
        audit_agent_name: Optional[str] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        query = bright_data_result.get("query", "")
        raw_results = bright_data_result.get("results", [])

        self._audit_start(
            audit_plugin=audit_plugin,
            audit_agent_name=audit_agent_name,
            query=query,
            raw_count=len(raw_results),
            audit_metadata=audit_metadata,
        )

        trusted_sources: List[Dict[str, Any]] = []
        usable_sources: List[Dict[str, Any]] = []
        lower_quality_sources: List[Dict[str, Any]] = []
        discarded_sources: List[Dict[str, Any]] = []

        seen_urls = set()

        for source in raw_results:
            normalized = self._normalize_source(source)
            url = normalized.get("url", "")

            if not url:
                discarded_sources.append(
                    self._with_decision(
                        normalized,
                        category="discarded",
                        reason="Missing source URL",
                        score=0,
                    )
                )
                continue

            if url in seen_urls:
                discarded_sources.append(
                    self._with_decision(
                        normalized,
                        category="discarded",
                        reason="Duplicate source URL",
                        score=0,
                    )
                )
                continue

            seen_urls.add(url)

            if self._is_blocked_source(normalized):
                discarded_sources.append(
                    self._with_decision(
                        normalized,
                        category="discarded",
                        reason="Blocked or non-content source",
                        score=0,
                    )
                )
                continue

            if self._is_lower_quality_source(normalized):
                lower_quality_sources.append(
                    self._with_decision(
                        normalized,
                        category="lower_quality",
                        reason="Social/community/user-generated source; keep only as weak signal",
                        score=25,
                    )
                )
                continue

            if self._is_trusted_source(normalized):
                trusted_sources.append(
                    self._with_decision(
                        normalized,
                        category="trusted",
                        reason="Recognized authoritative, institutional, or established news source",
                        score=90,
                    )
                )
                continue

            if self._is_usable_source(normalized):
                usable_sources.append(
                    self._with_decision(
                        normalized,
                        category="usable",
                        reason="Relevant industry, regional, trade, or specialist source",
                        score=70,
                    )
                )
                continue

            if self._has_enough_content(normalized):
                usable_sources.append(
                    self._with_decision(
                        normalized,
                        category="usable",
                        reason="Has title, URL, and snippet; usable pending LLM relevance review",
                        score=55,
                    )
                )
                continue

            lower_quality_sources.append(
                self._with_decision(
                    normalized,
                    category="lower_quality",
                    reason="Limited metadata or weak source signal",
                    score=35,
                )
            )

        trusted_sources = self._sort_sources(trusted_sources)[:max_trusted]
        usable_sources = self._sort_sources(usable_sources)[:max_usable]
        lower_quality_sources = self._sort_sources(lower_quality_sources)
        discarded_sources = self._sort_sources(discarded_sources)

        result = {
            "success": True,
            "query": query,
            "summary": {
                "rawResultCount": len(raw_results),
                "trustedCount": len(trusted_sources),
                "usableCount": len(usable_sources),
                "lowerQualityCount": len(lower_quality_sources),
                "discardedCount": len(discarded_sources),
                "evidenceReadyCount": len(trusted_sources) + len(usable_sources),
            },
            "trustedSources": trusted_sources,
            "usableSources": usable_sources,
            "lowerQualitySources": lower_quality_sources,
            "discardedSources": discarded_sources,
            "evidencePack": trusted_sources + usable_sources,
            "filterRules": {
                "trustedSources": "Official, institutional, established news, or recognized research sources",
                "usableSources": "Specialist, industry, regional, or content-rich sources",
                "lowerQualitySources": "Social/community/user-generated or weak-metadata sources",
                "discardedSources": "Duplicates, empty URLs, or blocked non-content sources",
            },
        }

        self._audit_final(
            audit_plugin=audit_plugin,
            audit_agent_name=audit_agent_name,
            result=result,
            audit_metadata=audit_metadata,
        )

        return result

    def _normalize_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        url = str(source.get("url") or source.get("link") or "").strip()
        domain = (
            str(source.get("sourceDomain") or source.get("displayLink") or "").strip()
            or self._extract_domain(url)
        )

        return {
            "rank": self._safe_int(source.get("rank"), 999),
            "title": str(source.get("title") or "").strip(),
            "url": url,
            "displayLink": str(source.get("displayLink") or "").strip(),
            "sourceDomain": domain,
            "snippet": str(source.get("snippet") or source.get("description") or "").strip(),
        }

    def _with_decision(
        self,
        source: Dict[str, Any],
        category: str,
        reason: str,
        score: int,
    ) -> Dict[str, Any]:
        return {
            **source,
            "sourceCategory": category,
            "qualityScore": score,
            "qualityReason": reason,
        }

    def _is_trusted_source(self, source: Dict[str, Any]) -> bool:
        domain_or_url = self._domain_or_url(source)
        return any(hint in domain_or_url for hint in self.TRUSTED_DOMAIN_HINTS)

    def _is_usable_source(self, source: Dict[str, Any]) -> bool:
        domain_or_url = self._domain_or_url(source)
        return any(hint in domain_or_url for hint in self.USABLE_DOMAIN_HINTS)

    def _is_lower_quality_source(self, source: Dict[str, Any]) -> bool:
        domain_or_url = self._domain_or_url(source)
        return any(hint in domain_or_url for hint in self.LOWER_QUALITY_DOMAIN_HINTS)

    def _is_blocked_source(self, source: Dict[str, Any]) -> bool:
        domain_or_url = self._domain_or_url(source)
        return any(hint in domain_or_url for hint in self.BLOCKED_DOMAIN_HINTS)

    def _has_enough_content(self, source: Dict[str, Any]) -> bool:
        return bool(source.get("title")) and bool(source.get("url")) and bool(source.get("snippet"))

    def _sort_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            sources,
            key=lambda item: (
                -int(item.get("qualityScore", 0)),
                int(item.get("rank", 999)),
            ),
        )

    def _domain_or_url(self, source: Dict[str, Any]) -> str:
        return (
            str(source.get("sourceDomain") or "")
            + " "
            + str(source.get("url") or "")
        ).lower()

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace("www.", "")
        except Exception:
            return ""

    @staticmethod
    def _safe_int(value: Any, fallback: int) -> int:
        try:
            return int(float(value))
        except Exception:
            return fallback

    def _audit_start(
        self,
        audit_plugin: Optional[Any],
        audit_agent_name: Optional[str],
        query: str,
        raw_count: int,
        audit_metadata: Optional[Dict[str, Any]],
    ) -> None:
        if audit_plugin is None:
            return

        audit_plugin.log(
            agent_name=audit_agent_name,
            stage="source_quality_filter_start",
            thought_content="Started source quality filtering for normalized Bright Data results.",
            stage_output={
                "query": query,
                "rawResultCount": raw_count,
            },
            metadata={
                **(audit_metadata or {}),
                "component": "source_quality_filter_plugin",
            },
        )

    def _audit_final(
        self,
        audit_plugin: Optional[Any],
        audit_agent_name: Optional[str],
        result: Dict[str, Any],
        audit_metadata: Optional[Dict[str, Any]],
    ) -> None:
        if audit_plugin is None:
            return

        audit_plugin.log(
            agent_name=audit_agent_name,
            stage="source_quality_filter_final_output",
            thought_content="Completed source quality filtering and prepared evidence pack.",
            stage_output={
                "summary": result.get("summary"),
                "trustedDomains": [
                    item.get("sourceDomain")
                    for item in result.get("trustedSources", [])[:5]
                ],
                "usableDomains": [
                    item.get("sourceDomain")
                    for item in result.get("usableSources", [])[:5]
                ],
                "lowerQualityDomains": [
                    item.get("sourceDomain")
                    for item in result.get("lowerQualitySources", [])[:5]
                ],
                "discardedCount": result.get("summary", {}).get("discardedCount"),
            },
            metadata={
                **(audit_metadata or {}),
                "component": "source_quality_filter_plugin",
            },
        )