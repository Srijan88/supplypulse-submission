import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from config.settings import settings


class BrightDataSearchPlugin:
    """
    Bright Data SERP Search Plugin for SupplyPulse V2.

    Responsibilities:
    - Send localized search queries to Bright Data SERP API.
    - Pass Google SERP localization correctly:
        gl = country
        hl = language
        uule = optional encoded location
    - Request structured JSON results.
    - Unwrap Bright Data response body.
    - Normalize organic results.
    - Write audit logs when audit_plugin is passed.
    """

    def __init__(self) -> None:
        self.api_key = settings.brightdata_api_key
        self.zone = settings.brightdata_serp_zone
        self.endpoint = settings.brightdata_serp_endpoint
        self.default_search_engine = settings.brightdata_default_search_engine
        self.default_country = settings.brightdata_default_country
        self.default_language = settings.brightdata_default_language
        self.default_location = settings.brightdata_default_location
        self.default_uule = settings.brightdata_default_uule

    def search(
        self,
        query: str,
        num_results: int = 10,
        country: Optional[str] = None,
        language: Optional[str] = None,
        location: Optional[str] = None,
        uule: Optional[str] = None,
        search_engine: Optional[str] = None,
        audit_plugin: Optional[Any] = None,
        audit_agent_name: Optional[str] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        resolved_country = self._normalize_country(country or self.default_country)
        resolved_language = self._normalize_language(language or self.default_language)
        resolved_location = self._clean_optional(location or self.default_location)
        resolved_uule = self._clean_optional(uule or self.default_uule)
        resolved_engine = (search_engine or self.default_search_engine or "google").lower()
        safe_num_results = self._safe_num_results(num_results)

        base_request_metadata = {
            "searchEngine": resolved_engine,
            "country": resolved_country,
            "gl": resolved_country,
            "language": resolved_language,
            "hl": resolved_language,
            "location": resolved_location,
            "uuleProvided": bool(resolved_uule),
            "zone": self.zone,
            "numResultsRequested": safe_num_results,
        }

        if not self.api_key:
            result = {
                "success": False,
                "query": query,
                "error": "BRIGHTDATA_API_KEY is missing in .env",
                "results": [],
                "requestMetadata": base_request_metadata,
            }
            self._audit_response(audit_plugin, audit_agent_name, result, audit_metadata)
            return result

        if not query or not query.strip():
            result = {
                "success": False,
                "query": query,
                "error": "Search query is empty",
                "results": [],
                "requestMetadata": base_request_metadata,
            }
            self._audit_response(audit_plugin, audit_agent_name, result, audit_metadata)
            return result

        target_url = self._build_search_url(
            query=query,
            num_results=safe_num_results,
            country=resolved_country,
            language=resolved_language,
            uule=resolved_uule,
            search_engine=resolved_engine,
        )

        payload = {
            "zone": self.zone,
            "url": target_url,
            "format": "json",
        }

        request_metadata = {
            **base_request_metadata,
            "query": query,
            "targetUrl": target_url,
            "endpoint": self.endpoint,
            "format": "json",
        }

        self._audit_request(
            audit_plugin=audit_plugin,
            audit_agent_name=audit_agent_name,
            request_metadata=request_metadata,
            audit_metadata=audit_metadata,
        )

        request = urllib.request.Request(
            url=self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                parsed_response = json.loads(response_body)

            unwrapped_response = self._unwrap_brightdata_response(parsed_response)
            normalized_results = self._extract_organic_results(unwrapped_response)

            result = {
                "success": True,
                "query": query,
                "targetUrl": target_url,
                "searchEngine": resolved_engine,
                "country": resolved_country,
                "language": resolved_language,
                "location": resolved_location,
                "uuleProvided": bool(resolved_uule),
                "zone": self.zone,
                "brightDataStatusCode": self._extract_status_code(parsed_response),
                "resultCount": len(normalized_results),
                "results": normalized_results[:safe_num_results],
                "requestMetadata": request_metadata,
                "responseMetadata": self._build_response_metadata(
                    parsed_response=parsed_response,
                    unwrapped_response=unwrapped_response,
                    normalized_results=normalized_results,
                ),
                "rawResponsePreview": self._build_raw_preview(parsed_response),
                "unwrappedPreview": self._build_raw_preview(unwrapped_response),
            }

            self._audit_response(
                audit_plugin=audit_plugin,
                audit_agent_name=audit_agent_name,
                result=result,
                audit_metadata=audit_metadata,
            )

            return result

        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            result = {
                "success": False,
                "query": query,
                "targetUrl": target_url,
                "statusCode": error.code,
                "error": error_body,
                "results": [],
                "requestMetadata": request_metadata,
            }
            self._audit_response(audit_plugin, audit_agent_name, result, audit_metadata)
            return result

        except urllib.error.URLError as error:
            result = {
                "success": False,
                "query": query,
                "targetUrl": target_url,
                "error": str(error.reason),
                "results": [],
                "requestMetadata": request_metadata,
            }
            self._audit_response(audit_plugin, audit_agent_name, result, audit_metadata)
            return result

        except json.JSONDecodeError as error:
            result = {
                "success": False,
                "query": query,
                "targetUrl": target_url,
                "error": f"Bright Data response was not valid JSON: {error}",
                "results": [],
                "requestMetadata": request_metadata,
            }
            self._audit_response(audit_plugin, audit_agent_name, result, audit_metadata)
            return result

        except Exception as error:
            result = {
                "success": False,
                "query": query,
                "targetUrl": target_url,
                "error": str(error),
                "results": [],
                "requestMetadata": request_metadata,
            }
            self._audit_response(audit_plugin, audit_agent_name, result, audit_metadata)
            return result

    def _build_search_url(
        self,
        query: str,
        num_results: int,
        country: str,
        language: str,
        uule: str,
        search_engine: str,
    ) -> str:
        safe_num_results = self._safe_num_results(num_results)

        if search_engine == "bing":
            params = {
                "q": query.strip(),
                "count": safe_num_results,
                "setlang": language,
                "cc": country,
            }
            return "https://www.bing.com/search?" + urllib.parse.urlencode(params)

        if search_engine == "duckduckgo":
            params = {
                "q": query.strip(),
                "kl": f"{country}-{language}",
            }
            return "https://duckduckgo.com/?" + urllib.parse.urlencode(params)

        params: Dict[str, Any] = {
            "q": query.strip(),
            "num": safe_num_results,
            "hl": language,
            "gl": country,
        }

        if uule:
            params["uule"] = uule

        return "https://www.google.com/search?" + urllib.parse.urlencode(params)

    def _unwrap_brightdata_response(self, parsed_response: Any) -> Any:
        if not isinstance(parsed_response, dict):
            return parsed_response

        if "body" not in parsed_response:
            return parsed_response

        body = parsed_response.get("body")

        if isinstance(body, dict) or isinstance(body, list):
            return body

        if isinstance(body, str):
            stripped_body = body.strip()

            parsed_json = self._try_parse_json(stripped_body)
            if parsed_json is not None:
                return parsed_json

            html_results = self._extract_results_from_html(stripped_body)
            if html_results:
                return {
                    "organic": html_results,
                    "source": "html_fallback_parser",
                }

            return {
                "rawBodyText": stripped_body[:5000],
                "source": "unparsed_body",
            }

        return parsed_response

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Any]:
        try:
            return json.loads(text)
        except Exception:
            return None

    def _extract_organic_results(self, parsed_response: Any) -> List[Dict[str, Any]]:
        candidate_items: List[Dict[str, Any]] = []

        if isinstance(parsed_response, dict):
            candidate_items.extend(self._extract_from_known_keys(parsed_response))
            candidate_items.extend(self._recursive_find_result_like_items(parsed_response))

        elif isinstance(parsed_response, list):
            for item in parsed_response:
                if isinstance(item, dict):
                    candidate_items.extend(self._extract_from_known_keys(item))
                    candidate_items.extend(self._recursive_find_result_like_items(item))

        normalized: List[Dict[str, Any]] = []
        seen_links = set()

        for item in candidate_items:
            if not isinstance(item, dict):
                continue

            title = self._first_present(item, ["title", "name", "heading"])
            link = self._first_present(item, ["link", "url", "href"])
            snippet = self._first_present(
                item,
                ["description", "snippet", "text", "content"],
            )
            display_link = self._first_present(
                item,
                ["display_link", "displayLink", "displayed_link", "source", "domain"],
            )
            rank = self._first_present(item, ["rank", "global_rank", "position"])

            if not title and not link and not snippet:
                continue

            if link and link in seen_links:
                continue

            if link:
                seen_links.add(link)

            normalized.append(
                {
                    "rank": self._safe_int(rank, len(normalized) + 1),
                    "title": str(title or "").strip(),
                    "url": str(link or "").strip(),
                    "displayLink": str(display_link or "").strip(),
                    "snippet": str(snippet or "").strip(),
                    "sourceDomain": self._extract_domain(str(link or "")),
                }
            )

        normalized.sort(key=lambda result: result.get("rank", 999))
        return normalized

    def _extract_from_known_keys(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        known_keys = [
            "organic",
            "organic_results",
            "organicResults",
            "organicResultsList",
            "results",
            "items",
            "search_results",
            "serp_results",
        ]

        for key in known_keys:
            value = data.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))

        return candidates

    def _recursive_find_result_like_items(self, data: Any) -> List[Dict[str, Any]]:
        found: List[Dict[str, Any]] = []

        if isinstance(data, dict):
            if self._looks_like_search_result(data):
                found.append(data)

            for value in data.values():
                found.extend(self._recursive_find_result_like_items(value))

        elif isinstance(data, list):
            for item in data:
                found.extend(self._recursive_find_result_like_items(item))

        return found

    @staticmethod
    def _looks_like_search_result(item: Dict[str, Any]) -> bool:
        has_title = any(key in item for key in ["title", "name", "heading"])
        has_link = any(key in item for key in ["link", "url", "href"])
        has_snippet = any(
            key in item for key in ["description", "snippet", "text", "content"]
        )

        return has_title and (has_link or has_snippet)

    def _extract_results_from_html(self, html: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        google_links = re.findall(r'href="/url\?q=(.*?)&amp;', html)

        for raw_link in google_links:
            decoded_link = urllib.parse.unquote(raw_link)

            if not decoded_link.startswith("http"):
                continue

            if "google.com" in decoded_link:
                continue

            results.append(
                {
                    "title": "",
                    "link": decoded_link,
                    "url": decoded_link,
                    "display_link": self._extract_domain(decoded_link),
                    "description": "",
                    "rank": len(results) + 1,
                }
            )

            if len(results) >= 10:
                break

        return results

    def _audit_request(
        self,
        audit_plugin: Optional[Any],
        audit_agent_name: Optional[str],
        request_metadata: Dict[str, Any],
        audit_metadata: Optional[Dict[str, Any]],
    ) -> None:
        if audit_plugin is None:
            return

        audit_plugin.log(
            agent_name=audit_agent_name,
            stage="bright_data_search_request",
            thought_content="Sending search query to Bright Data SERP API with localization parameters.",
            stage_output={
                "query": request_metadata.get("query"),
                "targetUrl": request_metadata.get("targetUrl"),
                "zone": request_metadata.get("zone"),
                "format": request_metadata.get("format"),
                "searchEngine": request_metadata.get("searchEngine"),
                "gl_country": request_metadata.get("gl"),
                "hl_language": request_metadata.get("hl"),
                "location": request_metadata.get("location"),
                "uuleProvided": request_metadata.get("uuleProvided"),
                "numResultsRequested": request_metadata.get("numResultsRequested"),
            },
            metadata={
                **(audit_metadata or {}),
                "component": "bright_data_search_plugin",
                "api_key_logged": False,
            },
        )

    def _audit_response(
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
            stage="bright_data_search_response",
            thought_content="Received Bright Data SERP response and normalized search evidence.",
            stage_output={
                "success": result.get("success"),
                "brightDataStatusCode": result.get("brightDataStatusCode")
                or result.get("statusCode"),
                "resultCount": result.get("resultCount", 0),
                "topSources": self.extract_top_sources(result, limit=5),
                "error": result.get("error"),
                "requestMetadata": result.get("requestMetadata"),
            },
            metadata={
                **(audit_metadata or {}),
                "component": "bright_data_search_plugin",
                "api_key_logged": False,
            },
        )

    def _build_response_metadata(
        self,
        parsed_response: Any,
        unwrapped_response: Any,
        normalized_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "brightDataStatusCode": self._extract_status_code(parsed_response),
            "rawPreview": self._build_raw_preview(parsed_response),
            "unwrappedPreview": self._build_raw_preview(unwrapped_response),
            "topSources": [
                result.get("sourceDomain") or result.get("displayLink")
                for result in normalized_results[:5]
            ],
        }

    @staticmethod
    def extract_top_sources(result: Dict[str, Any], limit: int = 5) -> List[str]:
        sources: List[str] = []

        for item in result.get("results", [])[:limit]:
            source = (
                item.get("sourceDomain")
                or item.get("displayLink")
                or BrightDataSearchPlugin._extract_domain(item.get("url", ""))
            )

            if source and source not in sources:
                sources.append(source)

        return sources

    @staticmethod
    def _first_present(item: Dict[str, Any], keys: List[str]) -> str:
        for key in keys:
            value = item.get(key)
            if value is not None and value != "":
                return str(value)
        return ""

    @staticmethod
    def _safe_num_results(value: Any) -> int:
        try:
            return max(1, min(int(value), 20))
        except Exception:
            return 10

    @staticmethod
    def _safe_int(value: Any, fallback: int) -> int:
        try:
            return int(float(value))
        except Exception:
            return fallback

    @staticmethod
    def _normalize_country(value: str) -> str:
        cleaned = str(value or "us").strip().lower()
        if len(cleaned) != 2:
            return "us"
        return cleaned

    @staticmethod
    def _normalize_language(value: str) -> str:
        cleaned = str(value or "en").strip().lower()
        if len(cleaned) < 2:
            return "en"
        return cleaned

    @staticmethod
    def _clean_optional(value: Optional[str]) -> str:
        return str(value or "").strip()

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc.replace("www.", "")
        except Exception:
            return ""

    @staticmethod
    def _extract_status_code(parsed_response: Any) -> Optional[int]:
        if isinstance(parsed_response, dict):
            status_code = parsed_response.get("status_code")
            try:
                return int(status_code)
            except Exception:
                return None
        return None

    @staticmethod
    def _build_raw_preview(parsed_response: Any) -> Dict[str, Any]:
        if isinstance(parsed_response, dict):
            preview: Dict[str, Any] = {
                "type": "dict",
                "topLevelKeys": list(parsed_response.keys())[:20],
            }

            if "status_code" in parsed_response:
                preview["status_code"] = parsed_response.get("status_code")

            if "body" in parsed_response:
                body = parsed_response.get("body")
                preview["bodyType"] = type(body).__name__

                if isinstance(body, str):
                    preview["bodyPreview"] = body[:500]

                if isinstance(body, dict):
                    preview["bodyKeys"] = list(body.keys())[:20]

            return preview

        if isinstance(parsed_response, list):
            return {
                "type": "list",
                "length": len(parsed_response),
            }

        if isinstance(parsed_response, str):
            return {
                "type": "str",
                "preview": parsed_response[:500],
            }

        return {
            "type": type(parsed_response).__name__,
        }