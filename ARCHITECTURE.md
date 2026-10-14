# CareerMark System Architecture

CareerMark follows a clean, modular structure focusing on deterministic evaluation backed by AI explanation.

## Core Modules

*   **`api/`:** Handles HTTP requests and routing (FastAPI).
*   **`core/`:** Contains business logic, the deterministic engine, and external service integrations (AI, Email).
*   **`db/`:** Manages SQLAlchemy models, schemas, and database sessions.
*   **`scripts/`:** Utility scripts for scraping, database resets, and testing.

## Database Schema (Relational Model)

*   **`User`:** Stores candidate profiles (e.g., degree, branch, graduation year).
*   **`Opportunity`:** Represents a job or internship (title, organization, closing date).
*   **`Requirement`:** Relational rules linked to Opportunities (e.g., `field_name="degree"`, `operator="=="`, `target_value="B.Tech"`).
*   **`Application`:** Tracks the state of a user's progress for a specific Opportunity.
*   **`NotificationOutbox`:** A durable queue for tracking and processing email alerts.

## The Deterministic Engine

The engine is the sole decision-maker for eligibility. It mathematically compares the `User` profile data against the `Requirement` table rules. AI is never allowed to override these decisions.

## AI Integration (Gemini)

1.  **Parsing:** Extracts structured JSON data from uploaded PDF resumes.
2.  **Explanation:** Generates human-readable context based *only* on the output of the Deterministic Engine.
