# Further Update: Evidence-Grounded Client Opportunity Intelligence Engine

**Status:** Approved for implementation\
**Priority:** High\
**Target:** Autonomous Economic Intelligence & Opportunity Engine

## 1. Objective

Add a first-class **Client Opportunity Intelligence** module for solo
freelancers, small teams, agencies, and consultancies.

The feature must discover, validate, qualify, enrich, rank, and explain
potential client opportunities across public and authorized Internet
sources.

It is **not** a generic lead scraper.

The intended product is:

> Evidence-Grounded Client Opportunity Intelligence.

Core loop:

``` text
User Profile
→ Services / ICP
→ Multi-Source Discovery
→ Buying-Signal Detection
→ Problem Detection
→ Source Validation
→ Entity Resolution
→ Intent Classification
→ Service Fit
→ Buyer Identification
→ Contact Enrichment
→ Opportunity Scoring
→ Why-Now Analysis
→ Evidence Dossier
→ Recommended Action
→ Outcome
→ Learning / Calibration
```

## 2. Product Principles

Optimize for **qualified, evidence-supported opportunities**, not lead
volume.

Every important assertion must preserve:

-   provenance
-   source URL/reference
-   exact evidence span where applicable
-   timestamp/freshness
-   confidence
-   epistemic status

Use the existing:

-   Internet acquisition/search/fetch
-   Agent Reach
-   provenance ledger
-   claims/classification
-   knowledge graph
-   opportunity engine
-   validation
-   research history
-   Research Director
-   controlled learning

Do not create duplicate infrastructure.

Do not modify FreeLLMAPI or OmniRoute internals.

## 3. User Modes

Support:

``` text
SOLO_FREELANCER
SMALL_TEAM
AGENCY
CONSULTANCY
```

User profile should define:

``` text
Services
Technologies
Industries
Target company size
Geographies
Languages
Minimum project value
Preferred project value
Delivery capacity
Technology strengths
Industry strengths
Portfolio/case studies
Differentiators
Preferred buyer roles
Exclusions
Availability
```

Users can select multiple services.

## 4. Discovery Modes

### Explicit Demand

Find direct public evidence such as:

-   looking for a developer
-   looking for an SEO specialist
-   need an automation expert
-   looking for an agency
-   vendor search
-   project request
-   outsourcing request

### Latent Opportunity

Detect organizations with evidence of problems that the user's services
could plausibly solve, even when they have not explicitly requested the
service.

Example:

``` text
Rapid growth
+
manual workflow
+
support expansion
+
no visible automation capability
=
Potential automation opportunity
```

Latent opportunities must be labeled `INFERENCE` or `HYPOTHESIS`, never
`FACT`.

## 5. Signal Taxonomy

Implement normalized signal types:

``` text
EXPLICIT_SERVICE_REQUEST
PROJECT_REQUEST
VENDOR_SEARCH
OUTSOURCING_SIGNAL
HIRING_SIGNAL
GROWTH_SIGNAL
FUNDING_SIGNAL
PRODUCT_LAUNCH
MARKET_EXPANSION
OPERATIONAL_FRICTION
TECHNOLOGY_GAP
MARKETING_GAP
SEO_GAP
AUTOMATION_GAP
WEBSITE_GAP
DATA_GAP
AI_ADOPTION_SIGNAL
EXECUTIVE_PAIN_SIGNAL
CUSTOMER_COMPLAINT_SIGNAL
REGULATORY_CHANGE_SIGNAL
PARTNERSHIP_SIGNAL
OTHER
```

Each signal stores:

``` text
signal_id
source_id
source_url
source_type
detected_at
published_at
signal_type
raw_evidence_span
normalized_signal
epistemic_status
confidence
freshness
```

## 6. Source Architecture

Use source adapters rather than hard-coded scraping.

Potential sources:

``` text
Search engines
Company websites
Official company blogs
Job boards
Public project boards
Public business directories
Public news
RSS/Atom
Public announcements
Public documentation
Public case studies
Permitted public forums
Licensed enrichment providers
Official APIs
User-authorized integrations
```

Each adapter declares:

``` text
source_name
acquisition_method
permission_model
supported_operations
coverage
freshness
reliability
rate_limits
authentication_requirement
```

### Mandatory boundary

Do not:

-   bypass authentication
-   bypass CAPTCHAs
-   circumvent rate limits
-   evade platform restrictions
-   scrape private content
-   collect private contact information
-   impersonate users
-   create fake accounts
-   harvest credentials
-   automate unsolicited mass outreach

For restricted platforms, use official APIs, licensed providers,
authorized integrations, or permitted public sources.

If unavailable, report `UNAVAILABLE`. Never fabricate coverage.

## 7. Discovery Pipeline

Implement:

``` text
Client Intelligence Request
→ Query / Signal Planning
→ Multi-Dimensional Search
→ Candidate Source Collection
→ Source Acquisition
→ Source Validation
→ Evidence Extraction
→ Signal Detection
→ Entity Resolution
→ Intent Classification
→ Problem Detection
→ Service Fit
→ Buyer Identification
→ Contact Enrichment
→ Economic Qualification
→ Opportunity Scoring
→ Dossier Generation
```

Reuse existing research infrastructure.

## 8. Search Planning

Do not use one generic query.

Generate dimensions based on the user's service.

For AI/automation:

``` text
AI hiring
AI implementation
AI product launch
manual workflows
support automation
internal copilots
automation gaps
operational scaling
outsourcing
vendor search
```

For SEO:

``` text
SEO hiring
organic traffic problems
website migration
international expansion
content scaling
traffic decline
new product pages
```

For web/software development:

``` text
website redesign
replatforming
legacy frontend
new product launch
conversion problems
software outsourcing
development vendor search
```

The planner should be extensible by service.

## 9. Entity Resolution

Create canonical:

``` text
Company
Person
Opportunity
Signal
Source
Contact Point
```

Multiple references to the same company/person must resolve to one
entity.

Do not merge on name similarity alone.

Company fields:

``` text
company_id
canonical_name
legal_name_if_available
domain
industry
size_estimate
geography
description
technology_signals
sources
last_verified_at
```

Person fields:

``` text
person_id
name
title
company_id
professional_profile
role_confidence
contact_points
sources
last_verified_at
```

## 10. Intent Classification

Classify:

``` text
DIRECT_BUYING_INTENT
LIKELY_BUYING_INTENT
POTENTIAL_OUTSOURCING
INTERNAL_HIRING
GENERAL_RESEARCH
LOW_INTENT
NO_RELEVANT_INTENT
UNKNOWN
```

The classification must include evidence and confidence.

Do not convert generic hiring into outsourcing intent.

## 11. Problem Detection

For latent opportunities:

``` text
Observed Signal
→ Operational Problem
→ Root-Cause Hypothesis
→ Affected Function
→ Economic Consequence
→ Potential Service Fit
```

Maintain strict epistemic boundaries:

``` text
OBSERVED
INFERRED
HYPOTHESIS
UNKNOWN
```

## 12. Service Fit

Compare:

``` text
Client Requirement
↕
User Capability Profile
```

Evaluate:

``` text
Technology Fit
Industry Fit
Problem Fit
Service Fit
Experience Fit
Portfolio Fit
Geography Fit
Budget Fit
Delivery Fit
```

Return:

``` text
service_fit_score
fit_explanation
matching_capabilities
missing_capabilities
evidence
confidence
```

Never claim a capability absent from the user's profile/evidence.

## 13. Buyer Identification

Potential roles:

``` text
Founder
CEO
COO
CTO
CIO
CMO
VP Engineering
VP Marketing
VP Growth
Head of SEO
Head of Operations
Head of Sales
Product Director
Procurement
Other
```

Assess:

``` text
PERSON_FOUND
ROLE_RELEVANT
DECISION_AUTHORITY_ESTIMATE
CONTACT_AVAILABLE
CONTACT_VERIFIED
```

Explain why the selected person is relevant.

## 14. Contact Enrichment

Create a provider abstraction:

``` text
ContactEnrichmentProvider
├── licensed provider
├── official API
├── public company contact
├── authorized integration
└── future providers
```

Contact types:

``` text
Professional profile
Business email
Business phone
Company contact page
Public professional contact
```

Every contact point stores:

``` text
contact_type
value
source
source_url
retrieved_at
verification_status
confidence
```

Verification states:

``` text
VERIFIED
PROBABLE
UNVERIFIED
STALE
INVALID
UNAVAILABLE
```

Never present guessed emails as verified.

Prefer business/professional contact information.

## 15. Opportunity Scoring

Implement a transparent deterministic score.

Conceptually:

``` text
Client Opportunity Score
=
Intent
× Problem Severity
× Service Fit
× Economic Potential
× Buyer Relevance
× Evidence Confidence
× Recency
× Accessibility
÷ Competitive Pressure
```

A weighted normalized implementation is acceptable if all components are
independently calculated.

Components:

``` text
intent_score
problem_severity_score
service_fit_score
economic_potential_score
buyer_relevance_score
evidence_confidence_score
recency_score
contact_accessibility_score
competitive_pressure_score
```

Every score requires:

``` text
value
calculation_method
evidence
confidence
```

Do not allow an LLM to invent the final score.

## 16. Why-Now Intelligence

Detect temporal triggers:

``` text
Recent funding
Recent hiring
Product launch
Market expansion
Leadership change
Website migration
Customer growth
Operational expansion
Public complaint
Vendor search
Project request
```

Return:

``` text
why_now
trigger_date
trigger_source
freshness
confidence
```

## 17. Economic Qualification

Where evidence supports it, estimate:

``` text
Potential project value
Potential recurring value
Economic pain
Potential ROI
Urgency
Budget likelihood
```

Every financial value must be:

``` text
OBSERVED
CALCULATED
ESTIMATED
ASSUMED
UNKNOWN
```

Never invent prospect budgets.

## 18. Opportunity Dossier

Every qualified opportunity should have:

``` text
Opportunity
├── Executive Summary
├── Company
├── Detected Need
├── Buying Signals
├── Why Now
├── Evidence
├── Problem Analysis
├── Service Fit
├── Economic Potential
├── Likely Buyer
├── Contact Information
├── Contact Verification
├── Competition
├── Risks
├── Unknowns
├── Confidence
├── Recommended Action
└── Sources
```

Evidence trace must be:

``` text
Opportunity
→ Problem
→ Claim
→ Source
→ Exact Evidence Span
→ Provenance Hash
```

## 19. Opportunity Lifecycle

Persist:

``` text
DISCOVERED
→ VALIDATED
→ QUALIFIED
→ CONTACT_IDENTIFIED
→ CONTACTED
→ REPLIED
→ MEETING
→ PROPOSAL
→ WON
```

Alternative terminal state:

``` text
LOST
```

Suppression states:

``` text
DO_NOT_CONTACT
NOT_A_FIT
DUPLICATE
ALREADY_CONTACTED
EXISTING_CLIENT
COMPETITOR
EXPIRED
```

## 20. Deduplication and Freshness

Store:

``` text
first_detected_at
last_seen_at
last_verified_at
published_at
signal_age
freshness_score
```

Opportunity states:

``` text
ACTIVE
AGING
STALE
EXPIRED
UNKNOWN
```

The same company appearing across multiple sources must not create
duplicate opportunities.

## 21. Competitive Context

Estimate, where evidence permits:

``` text
competition_pressure
known competing vendors
internal capability
market saturation
```

Do not claim "no competition" without strong evidence.

Use `POTENTIAL_MARKET_GAP` when appropriate.

## 22. Recommended Action

Possible actions:

``` text
CONTACT_NOW
RESEARCH_BEFORE_CONTACT
IDENTIFY_BETTER_BUYER
VALIDATE_NEED
WAIT_FOR_TRIGGER
DO_NOT_CONTACT
```

The action must reflect evidence and uncertainty.

## 23. Outreach Intelligence

Generate an intelligence brief, not automatic spam:

``` text
Who they are
What changed
Observed problem
Evidence
Why the user's service is relevant
Likely buyer
Suggested conversation angle
Claims to avoid
Questions to ask
```

Do not invent familiarity or unsupported pain.

Automatic outbound messaging is out of scope for the first release.

## 24. UI

Add a top-level:

``` text
Client Intelligence
```

Input:

``` text
Operating Model:
○ Solo Freelancer
○ Small Team
○ Agency
○ Consultancy

Services:
[ AI Development ▼ ]

Industries:
[ SaaS ] [ E-commerce ]

Geography:
[ Worldwide ▼ ]

Minimum Project Value:
[ Optional ]

Discovery:
○ Explicit Demand
○ Latent Opportunities
● Both

[ FIND CLIENT OPPORTUNITIES ]
```

Results should prioritize:

``` text
Opportunity Score
Intent
Evidence Confidence
Freshness
Service Fit
Why Now
Likely Buyer
Contact Availability
```

Opportunity detail should contain:

``` text
Overview
Why This Opportunity
Evidence
Problem
Service Fit
Economic Analysis
Buyer
Contact Verification
Competitive Context
Risks
Unknowns
Recommended Action
Sources
Audit / Provenance
```

Use the existing premium light institutional design.

## 25. APIs

Implement equivalents consistent with the existing API conventions:

``` http
GET  /api/client-intelligence/profile
POST /api/client-intelligence/profile
PUT  /api/client-intelligence/profile

POST /api/client-intelligence/search
GET  /api/client-intelligence/opportunities
GET  /api/client-intelligence/opportunities/{id}

POST /api/client-intelligence/opportunities/{id}/qualify
POST /api/client-intelligence/opportunities/{id}/validate

GET  /api/client-intelligence/opportunities/{id}/contacts
POST /api/client-intelligence/opportunities/{id}/enrich

POST /api/client-intelligence/opportunities/{id}/status
POST /api/client-intelligence/opportunities/{id}/suppress

GET  /api/client-intelligence/opportunities/{id}/dossier
GET  /api/client-intelligence/opportunities/{id}/sources
GET  /api/client-intelligence/opportunities/{id}/provenance

POST /api/client-intelligence/opportunities/{id}/outcome
GET  /api/client-intelligence/outcomes
```

Adapt names if the existing project has a different API convention.

## 26. Suggested Schemas

Create equivalents of:

``` text
ClientIntelligenceProfile
ClientIntelligenceSearchRequest
ClientIntelligenceSearchRun
OpportunitySignal
ClientCompany
ClientPerson
ContactPoint
ContactVerification
ServiceFitAssessment
BuyerAssessment
OpportunityScore
WhyNowAssessment
ClientOpportunity
ClientOpportunityDossier
OpportunityOutcome
OpportunityFeedback
```

Use:

``` text
run_id
source_id
provenance_id
confidence
epistemic_status
timestamps
```

where applicable.

## 27. Database

Use the existing relational persistence layer.

Suggested tables:

``` text
client_profiles
client_services
client_target_markets
client_search_runs
client_signals
client_companies
client_people
client_contacts
client_opportunities
client_opportunity_sources
client_opportunity_claims
client_opportunity_scores
client_opportunity_events
client_outcomes
client_suppressions
client_enrichment_attempts
```

Connect to existing:

``` text
research_runs
sources
documents
claims
spans
provenance
```

Use migrations.

Never delete historical research data.

## 28. Knowledge Graph

Add first-class entities:

``` text
CLIENT_PROFILE
COMPANY
PERSON
CONTACT
BUYING_SIGNAL
CLIENT_OPPORTUNITY
SERVICE
PROBLEM
TRIGGER_EVENT
```

Relationships:

``` text
PROFILE_OFFERS_SERVICE
PROFILE_TARGETS_INDUSTRY
COMPANY_EXHIBITS_SIGNAL
SIGNAL_SUPPORTS_OPPORTUNITY
COMPANY_HAS_PROBLEM
PROBLEM_MATCHES_SERVICE
PERSON_WORKS_AT_COMPANY
PERSON_MAY_OWN_PROBLEM
PERSON_HAS_CONTACT
OPPORTUNITY_SUPPORTED_BY_CLAIM
CLAIM_SUPPORTED_BY_SOURCE
OPPORTUNITY_TRIGGERED_BY_EVENT
OPPORTUNITY_SUPPRESSED_BY_USER
OPPORTUNITY_RESULTED_IN_OUTCOME
```

Keep the default graph view macro/strategic rather than a giant evidence
cloud.

## 29. Research History Integration

Every client-intelligence run becomes persistent Research History:

``` text
objective
profile
services
ICP
queries
sources
signals
companies
people
opportunities
uncertainties
recommendations
outcomes
```

Do not rediscover already resolved or suppressed opportunities
unnecessarily.

## 30. Research Director Integration

Reuse the existing Research Director.

Possible next investigations:

``` text
Verify buying intent
Find a better decision-maker
Investigate budget
Verify technology stack
Find competing vendors
Check whether project is active
Validate problem
Find independent corroboration
Check recency
Investigate outsourcing history
```

Use the existing priority principle:

``` text
Expected Information Gain
× Economic Relevance
× Uncertainty
× Actionability
÷ Research Cost
```

Expected information gain must have a defensible basis/evidence.

## 31. Adversarial Validation

For important opportunities ask:

``` text
Why might this NOT be a real opportunity?
Could this be internal hiring?
Could the problem be insignificant?
Could the company already have a vendor?
Could the buyer be wrong?
Could the evidence be stale?
Could the inferred problem be wrong?
Is there sufficient economic value?
Is the service actually needed?
```

Return:

``` text
CONFIRMED
LIKELY
UNCERTAIN
WEAK
REJECTED
```

Do not force positive conclusions.

## 32. Security and Data Governance

Internet content is untrusted data.

Never allow web content to override application instructions or security
policy.

Sanitize:

``` text
HTML
scripts
embedded prompts
malicious instructions
unexpected URLs
```

Do not execute arbitrary code from sources.

For contact data, store:

``` text
source
collection timestamp
purpose
verification status
retention policy
deletion capability
```

Minimize personal data and prefer business/professional contact
information.

Provide controls for:

``` text
Delete opportunity
Delete contact
Suppress company
Suppress person
Delete search history
Export client intelligence data
```

## 33. Cost and Rate Controls

Implement:

``` text
per-run source budget
per-provider request budget
per-user search budget
maximum candidates
maximum enrichment attempts
maximum LLM calls
```

Use adaptive budgets.

High-intent searches can use smaller budgets; ambiguous
latent-opportunity research can receive larger budgets only when
justified.

## 34. Learning and Outcome Feedback

Store:

``` text
prediction
opportunity_score
confidence
recommended_action
contacted
response
meeting
proposal
won
lost
revenue_if_known
loss_reason_if_known
user_feedback
```

Learning lifecycle:

``` text
Experience Store
→ Quality Filter
→ Human / Evaluator Review
→ Curated Dataset
→ Evaluation
→ Training
→ Locked Evaluation
→ Model Registry
→ Shadow Deployment
→ Promotion
```

Never automatically fine-tune production from raw prospect outcomes.

## 35. Required Tests

Add at least:

``` text
test_client_profile.py
test_client_discovery.py
test_client_signal_detection.py
test_client_intent_classification.py
test_client_entity_resolution.py
test_client_service_fit.py
test_client_buyer_identification.py
test_client_contact_enrichment.py
test_client_contact_verification.py
test_client_opportunity_scoring.py
test_client_opportunity_deduplication.py
test_client_freshness.py
test_client_provenance.py
test_client_lifecycle.py
test_client_outcomes.py
test_client_suppression.py
test_client_research_history.py
test_client_research_director_integration.py
test_client_security.py
test_client_source_permissions.py
test_client_adversarial_validation.py
```

Critical adversarial cases:

``` text
Generic hiring ≠ outsourcing
Old request → stale/expired
Five sources for one company → one entity
Same requirement across sources → one opportunity
Growth signal → inference, not fact
No budget evidence → UNKNOWN
Guessed email → UNVERIFIED
Conflicting sources → unresolved contradiction
Restricted source → no bypass
Prompt injection in webpage → treated as untrusted content
```

## 36. Evaluation Metrics

Track:

``` text
Source precision
Opportunity precision
Opportunity recall
Intent accuracy
Entity-resolution accuracy
Contact-verification precision
Buyer-role accuracy
Service-fit accuracy
False-positive rate
Duplicate rate
Stale-opportunity rate
Evidence coverage
Provenance coverage
Outcome conversion rate
Score calibration
Precision@10
Precision@25
```

Do not optimize for raw lead count.

## 37. Outcome Analytics

Once real usage exists, track:

``` text
opportunities discovered
qualified
contacts identified
contacted
responses
meetings
proposals
wins
losses
revenue
conversion by score band
conversion by signal type
conversion by industry
conversion by service
conversion by buyer role
```

Do not claim predictive accuracy until outcomes validate the scoring
model.

## 38. Implementation Phases

### Phase 1 --- Foundation

Profiles, schemas, persistence, migrations, source/provenance
integration.

### Phase 2 --- Discovery

Multi-dimensional search, signal detection, candidate generation.

### Phase 3 --- Qualification

Intent, problem detection, service fit, buyer identification, economics.

### Phase 4 --- Enrichment

Entity resolution, contact providers, verification, freshness,
deduplication.

### Phase 5 --- Intelligence

Scoring, why-now, adversarial validation, dossier, recommended action.

### Phase 6 --- UI

Client Intelligence tab, search, filters, results, dossier, evidence
viewer.

### Phase 7 --- Memory

Research History, opportunity history, suppressions, outcomes.

### Phase 8 --- Research Director

Connect unresolved client-intelligence uncertainty to existing Research
Director.

### Phase 9 --- Outcome Learning

Outcome tracking and curated learning-data generation.

## 39. Explicitly Out of Scope for V1

Do not implement:

``` text
Automatic mass outreach
Automatic LinkedIn messaging
Automatic Instagram messaging
Automatic account creation
CAPTCHA bypass
Private-profile scraping
Credential collection
Unrestricted platform crawling
Bulk personal-email harvesting
Autonomous proposal submission
Autonomous contracting
Autonomous purchasing
```

## 40. Definition of Done

The feature is complete only when:

-   Freelancer/agency operating mode works.
-   Services and ICP can be configured.
-   Explicit-demand discovery works.
-   Latent-opportunity discovery works.
-   Multi-dimensional discovery works.
-   Sources are provenance-tracked.
-   Claims are evidence-linked.
-   Companies/persons are entity-resolved.
-   Duplicate opportunities are merged.
-   Intent is classified.
-   Internal hiring is distinguished from outsourcing.
-   Service fit is calculated.
-   Buyer relevance is calculated.
-   Contact information is source-tracked.
-   Contact verification status is visible.
-   Financial estimates are epistemically labeled.
-   Opportunity scoring is transparent and reproducible.
-   Score components are inspectable.
-   Why-now analysis is evidence-backed.
-   Stale opportunities are detected.
-   Adversarial validation works.
-   Recommended action is produced.
-   Opportunity dossier works.
-   Evidence/provenance chain is inspectable.
-   Suppression controls work.
-   Outcomes can be recorded.
-   Research History is preserved.
-   Research Director can recommend next investigations.
-   Security controls work.
-   Restricted sources are not bypassed.
-   No credentials are exposed.
-   Existing infrastructure is reused.
-   Existing tests still pass.
-   New tests pass.
-   Browser verification passes end-to-end.
-   No fake metrics/data are introduced.

## 41. Agent Execution Instructions

When implementing this document:

1.  Inspect the existing codebase before modifying it.
2.  Reuse existing abstractions.
3.  Do not duplicate
    search/fetch/provenance/knowledge/opportunity/validation/history
    infrastructure.
4.  Do not modify FreeLLMAPI internals.
5.  Do not modify OmniRoute internals.
6.  Keep third-party infrastructure modular and replaceable.
7.  Preserve existing behavior and tests.
8.  Use migrations for database changes.
9.  Preserve historical data.
10. Never fabricate populated demo data to hide missing functionality.
11. Do not hardcode opportunity/source/contact/claim counts.
12. Keep every material assertion evidence-traceable.
13. Label every inference.
14. Label every estimate with assumptions and confidence.
15. Preserve UNKNOWN where evidence is insufficient.
16. Respect source permissions and platform restrictions.
17. Never expose secrets.
18. Add unit/integration/adversarial tests.
19. Run the full existing test suite.
20. Perform browser-level verification.
21. Verify cross-run persistence, deduplication, and suppression.
22. Verify reproducible scoring.
23. Verify opportunity → claim → source → span → provenance tracing.
24. Verify inference cannot silently become fact.
25. Produce an implementation report containing:
    -   files changed
    -   migrations
    -   APIs
    -   UI components
    -   tests
    -   test results
    -   known limitations
    -   source-coverage limitations
    -   remaining risks

Do not stop at UI mockups. The feature is complete only when discovery,
evidence, qualification, enrichment, scoring, provenance, persistence,
validation, history, and outcome tracking work end-to-end.
