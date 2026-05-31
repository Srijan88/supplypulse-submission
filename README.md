# SupplyPulse

## AI Delivery Exposure Platform

SupplyPulse is an AI-powered delivery exposure platform for enterprise supply chain teams managing critical equipment deliveries across global suppliers, countries, and routes.

It helps teams identify high-pressure equipment deliveries, understand why those deliveries need attention, verify the external evidence behind the findings, and generate business-ready reports.

---

## Demo Workspace

**Customer:** NorthBridge Energy Infrastructure  
**Program:** Singapore Data Center Phase 2

For the demo, SupplyPulse is connected to a delivery dataset containing:

- 20 equipment delivery items
- Planned need dates
- Forecast arrival dates
- Delay / gain in days
- Source countries
- Destination countries
- External search queries for geopolitical, trade / tariff, and route logistics analysis

---

## The Problem

Global equipment deliveries are becoming harder to control.

Large infrastructure and construction projects depend on critical equipment arriving on time, but delivery teams still track schedule pressure, country issues, trade rules, customs updates, port congestion, and logistics disruptions manually.

Projects source equipment from many suppliers across different countries and shipping routes. External conditions can change overnight, and teams often rely on spreadsheets, supplier emails, expediters, and manual research to understand what is happening.

As a result, delivery pressure is often found too late. Timelines slip, urgent shipping costs increase, teams spend more time reacting, and stakeholder confidence drops.

**Teams are not short of data. They are short of early, evidence-backed delivery signals.**

---

## The Solution

SupplyPulse turns static delivery data into an evidence-backed delivery workflow.

The platform helps teams answer:

> Which equipment deliveries need attention, why are they under pressure, and what should our team do next?

SupplyPulse combines internal delivery data with external web evidence. It uses specialized AI agents, Gemini as the LLM reasoning layer, Bright Data API for external evidence, and source quality filtering to generate clear, traceable business insights.

---

## What “Exposure” Means

In SupplyPulse, **exposure means delivery pressure**.

It shows where a shipment or equipment item may be delayed, blocked, or affected by outside problems such as:

- Schedule delay
- Country or regional issues
- Customs or tariff changes
- Trade agreement changes
- Port congestion
- Shipping route disruption
- Weather or logistics bottlenecks

**Schedule Exposure % is a delay-pressure score, not a probability.**

A high value means the delivery timeline needs attention.

---

## Key Capabilities

- Ask natural-language delivery questions
- Identify high-exposure equipment deliveries
- Calculate Schedule Exposure %
- Separate schedule, geopolitical, trade / tariff, and route logistics exposure
- Use Bright Data API to gather fresh external web evidence
- Filter sources before sending evidence to the LLM
- Use Gemini to reason over filtered evidence
- Generate executive summaries, findings, recommendations, and limitations
- Visualize route pressure on a supply map
- Provide a traceable audit trail for every agent run
- Export a business-ready PDF report

---

## Product Workflow

```text
User Question
    ↓
Router Agent
    ↓
Schedule Analyzer Agent
    ↓
External Exposure Agents
    ├── Geopolitical Analyst Agent
    ├── Trade / Tariff Analyst Agent
    └── Route / Logistics Analyst Agent
    ↓
Bright Data Search
    ↓
Source Quality Filter
    ↓
Gemini Evidence Assessment
    ↓
Report Builder Agent
    ↓
Control Tower / Supply Map / Evidence / Reports / Audit Trail
```

---

## Agent Pipeline

### 1. Router Agent

The Router Agent understands the user’s question and decides which downstream agents should run.

Example question:

```text
Give me complete external exposure analysis for high schedule exposure items including geopolitical, trade tariff, and route logistics exposure.
```

The Router Agent identifies that schedule, geopolitical, trade / tariff, route logistics, and report generation are needed.

---

### 2. Schedule Analyzer Agent

The Schedule Analyzer Agent reads the loaded delivery data and calculates schedule pressure for each equipment item.

It produces:

- Delivery Exposure Table
- Planned Need Date
- Forecast Arrival
- Delay / Gain
- Schedule Exposure %
- Status Band
- Source Country
- Destination Country
- External search queries

---

### 3. Geopolitical Analyst Agent

The Geopolitical Analyst Agent checks country and regional issues that may affect high-exposure delivery items.

It uses Bright Data search results and filtered evidence to assess country-related exposure.

---

### 4. Trade / Tariff Analyst Agent

The Trade / Tariff Analyst Agent checks customs, tariff, duty, import, and trade agreement exposure.

It helps procurement and compliance teams understand whether trade rules may affect delivery timelines.

---

### 5. Route / Logistics Analyst Agent

The Route / Logistics Analyst Agent checks route, port, congestion, shipping, weather, and logistics-related issues.

It helps logistics teams understand whether delivery pressure is connected to route-level disruption.

---

### 6. Report Builder Agent

The Report Builder Agent combines schedule analysis, external exposure findings, evidence, recommendations, limitations, and audit context into a business-ready report.

---

## Gemini and Bright Data Usage

### Gemini

Gemini is used as the LLM reasoning layer inside the agent workflow.

It helps with:

- Understanding the user’s business question
- Interpreting delivery and schedule context
- Assessing filtered external evidence
- Generating exposure summaries
- Producing key findings
- Creating recommended actions
- Writing limitations
- Building the final business report narrative

### Bright Data API

Bright Data API is used to collect fresh external web evidence.

SupplyPulse uses it to search for:

- Geopolitical signals
- Country and regional disruption
- Tariff and customs information
- Trade agreement information
- Port congestion
- Shipping disruption
- Logistics bottlenecks
- Weather and seasonal route issues

### Source Quality Filter

SupplyPulse does not blindly trust every search result.

After Bright Data returns results, the Source Quality Filter separates:

- Trusted sources
- Usable sources
- Lower-quality sources
- Evidence-ready sources

Only evidence-ready sources are passed into the LLM assessment.

---

## Main Screens

### Login

A professional workspace entry screen for the NorthBridge Energy Infrastructure demo environment.

### Ask SupplyPulse

The main AI assistant screen.

Users can ask delivery exposure questions in natural language and run the agent pipeline.

Example question:

```text
Give me complete external exposure analysis for high schedule exposure items including geopolitical, trade tariff, and route logistics exposure.
```

---

### Control Tower

The delivery dashboard showing the Delivery Exposure Table.

Key fields:

- Item Code
- Asset / Equipment
- Planned Need Date
- Forecast Arrival
- Delay / Gain
- Schedule Exposure %
- Status Band
- Source Country
- Destination Country

---

### Supply Map

A Google Maps-powered route view that visualizes delivery pressure by source and destination country.

It shows:

- Source countries
- Destination countries
- Route lines
- Affected equipment items
- Schedule Exposure %
- Geopolitical exposure
- Trade / tariff exposure
- Route / logistics exposure

---

### Exposure Workspace

Separates external exposure into three business areas:

- Geopolitical Exposure
- Trade / Tariff Exposure
- Route / Logistics Exposure

This helps operations, procurement, compliance, and logistics teams understand the cause of delivery pressure.

---

### Evidence

Shows the evidence behind the answer.

It includes:

- Bright Data search queries
- Raw result counts
- Trusted sources
- Usable sources
- Lower-quality sources
- Evidence-ready sources
- Source titles
- Domains
- Evidence summaries
- Relevance reasons

---

### Reports

Creates a business-ready report with:

- Executive summary
- Exposure overview
- Delivery Exposure Table
- Geopolitical exposure section
- Trade / tariff exposure section
- Route / logistics exposure section
- Evidence used
- Recommended actions
- Limitations
- Run audit summary

The report can be exported as PDF, while markdown export is also available for technical review.

---

### Audit Trail

Shows what happened during the AI pipeline.

It includes:

- Total audit logs
- Shared run ID
- Agent audit counts
- Stage timeline
- Evidence search summary
- Agent output summary

This makes the workflow traceable from question to evidence to final report.

---

## Business Impact

SupplyPulse helps enterprise teams move from manual delivery tracking to evidence-backed delivery decisions.

### Faster Detection

Identify high-pressure deliveries earlier.

### Better Clarity

Separate schedule, country, trade, and route issues clearly.

### Less Manual Research

Reduce dependency on manual news monitoring, supplier emails, and spreadsheet tracking.

### Evidence-Backed Decisions

Use filtered external evidence instead of unsupported assumptions.

### Better Reporting

Generate business-ready summaries and PDF reports for stakeholders.

### Traceability

Use audit trails and shared run IDs to understand how each result was produced.

---

## Architecture

```text
Frontend
Next.js + TypeScript + Tailwind CSS + Google Maps
        ↓
Backend API
FastAPI
        ↓
Agent Pipeline
Router → Schedule → Geo → Trade → Route → Report
        ↓
External Intelligence
Bright Data API
        ↓
Source Quality Filter
Trusted / Usable / Lower-Quality / Evidence-Ready
        ↓
LLM Reasoning
Gemini
        ↓
Outputs
Dashboard + Map + Evidence + PDF Report + Audit Trail
```

---

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Google Maps JavaScript API
- `@vis.gl/react-google-maps`
- Lucide React icons

### Backend

- Python
- FastAPI
- Gemini / Vertex AI
- Bright Data API
- Source Quality Filter
- Agent audit logging
- Report generation logic

### Development and Deployment

- GitHub
- Vercel for frontend
- Railway for backend
- Environment variables for API keys and secrets

---

## Project Structure

```text
SupplyPulse/
├── backend/
│   ├── agents/
│   │   ├── router_agent.py
│   │   ├── schedule_analyzer_agent.py
│   │   ├── geo_risk_analyst_agent.py
│   │   ├── trade_risk_analyst_agent.py
│   │   ├── route_risk_analyst_agent.py
│   │   ├── risk_report_builder_agent.py
│   │   └── support_agent.py
│   ├── plugins/
│   │   ├── audit_logging_plugin.py
│   │   ├── audit_flow_plugin.py
│   │   ├── bright_data_search_plugin.py
│   │   ├── source_quality_filter_plugin.py
│   │   ├── schedule_data_plugin.py
│   │   ├── schedule_risk_plugin.py
│   │   └── search_query_plugin.py
│   ├── config/
│   │   └── settings.py
│   ├── data/
│   │   └── supplypulse_raw_supply_chain_items.csv
│   ├── api_server.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   ├── components/
│   │   ├── AskSupplyPulse.tsx
│   │   ├── AuditTrail.tsx
│   │   ├── ControlTower.tsx
│   │   ├── EvidencePanel.tsx
│   │   ├── ExposureWorkspace.tsx
│   │   ├── LoginScreen.tsx
│   │   ├── ReportsPanel.tsx
│   │   ├── Shell.tsx
│   │   └── SupplyMap.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── sampleData.ts
│   │   └── types.ts
│   ├── package.json
│   ├── next.config.ts
│   ├── postcss.config.mjs
│   ├── tsconfig.json
│   └── .env.local.example
│
├── README.md
└── .gitignore
```

---

## Environment Variables

Do not commit real environment files or API keys.

### Backend

Create:

```text
backend/.env
```

Use this template:

```env
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

RAW_DATA_PATH=./data/supplypulse_raw_supply_chain_items.csv

BRIGHTDATA_API_KEY=your-brightdata-api-key
BRIGHTDATA_SERP_ZONE=serp
BRIGHTDATA_SERP_ENDPOINT=https://api.brightdata.com/request
BRIGHTDATA_DEFAULT_SEARCH_ENGINE=google
BRIGHTDATA_DEFAULT_COUNTRY=us
BRIGHTDATA_DEFAULT_LANGUAGE=en
BRIGHTDATA_DEFAULT_LOCATION=
BRIGHTDATA_DEFAULT_UULE=
```

### Frontend

Create:

```text
frontend/.env.local
```

Use this template:

```env
NEXT_PUBLIC_SUPPLYPULSE_API_BASE=http://127.0.0.1:8000
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

---

## Running Locally

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api_server:app --reload --port 8000
```

Backend health check:

```text
http://127.0.0.1:8000/api/health
```

---

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3001
```

If Next.js starts on a different port, use the port shown in the terminal.

---

## Deployment Plan

Recommended production architecture:

```text
Frontend: Vercel
Backend: Railway
Repository: GitHub
```

### Vercel Frontend

Add these environment variables in Vercel:

```env
NEXT_PUBLIC_SUPPLYPULSE_API_BASE=https://your-railway-backend-url
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### Railway Backend

Add backend environment variables in Railway:

```env
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
BRIGHTDATA_API_KEY=your-brightdata-api-key
BRIGHTDATA_SERP_ZONE=serp
BRIGHTDATA_SERP_ENDPOINT=https://api.brightdata.com/request
BRIGHTDATA_DEFAULT_SEARCH_ENGINE=google
BRIGHTDATA_DEFAULT_COUNTRY=us
BRIGHTDATA_DEFAULT_LANGUAGE=en
RAW_DATA_PATH=./data/supplypulse_raw_supply_chain_items.csv
```

Recommended Railway start command:

```bash
python -m uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

Before live deployment, update backend CORS to allow the deployed Vercel URL.

---

## Security Notes

Never commit:

- `.env`
- `.env.local`
- `service-account.json`
- Google service account keys
- Bright Data API keys
- Google Maps API keys
- private keys or credentials

Use `.env.example` and `.env.local.example` files with placeholder values only.

If a real key is accidentally committed, rotate the key immediately before making the repository public.

---

## Responsible AI and Explainability

SupplyPulse is designed for traceable AI-assisted decision support.

It includes:

- Agent stage logging
- Shared run ID
- Evidence search summary
- Source quality filtering
- Agent output summaries
- Report limitations
- Audit trail for every major step

The system is not intended to replace human decision-makers. It helps teams identify delivery pressure earlier, inspect evidence, and make more informed decisions.

---

## Example Demo Flow

1. Login to the NorthBridge workspace.
2. Open Ask SupplyPulse.
3. Ask for complete external exposure analysis.
4. Review the completed agent result.
5. Open Control Tower to inspect the Delivery Exposure Table.
6. Open Supply Map to view route pressure visually.
7. Open Exposure Workspace to review country, trade, and route findings.
8. Open Evidence to inspect Bright Data results and source quality.
9. Open Reports to export the PDF report.
10. Open Audit Trail to verify the run.

---

## Short Project Description

SupplyPulse is an AI delivery exposure platform that helps teams find high-pressure equipment deliveries, connect delays to Bright Data-backed external evidence, and generate traceable reports for faster action.

---

## Long Project Description

SupplyPulse is an AI-powered delivery exposure platform for enterprise supply chain teams managing critical equipment deliveries across global suppliers, countries, and routes. The platform helps teams identify high-pressure deliveries, understand why they need attention, verify the external evidence behind the findings, and generate business-ready reports.

For the demo, SupplyPulse is connected to the NorthBridge Energy Infrastructure workspace for the Singapore Data Center Phase 2 program. It analyzes equipment delivery records, planned need dates, forecast arrivals, source countries, destination countries, and external exposure queries.

The user can ask one business question, and SupplyPulse runs an agent pipeline that checks schedule pressure, geopolitical issues, trade and tariff exposure, and route logistics concerns. Bright Data API is used to gather fresh external web evidence, a Source Quality Filter keeps useful sources, and Gemini reasons over the filtered evidence to generate summaries, recommendations, limitations, reports, and an audit trail.

SupplyPulse turns static delivery tracking into an evidence-backed workflow for faster, more confident supply chain decisions.

---

## License

Add your selected license here.

Recommended options:

- MIT License for simple open-source release
- Apache License 2.0 for a more formal open-source release
- Private repository if the project contains proprietary implementation details
