```markdown
## System Patterns (systemPatterns.md)

This document outlines the system patterns used in the "Arsa analiz ve sunum projesi" (Land Analysis and Presentation Project). It covers the architectural design, data models, API definitions, component structure, integration points, and scalability strategy of the web application.

### 1. Architectural Design: Microservices Architecture

We will employ a microservices architecture to achieve modularity, scalability, and independent deployment. Each microservice will handle a specific domain responsibility, such as data ingestion, analysis, visualization, and user authentication.

**Rationale:**

*   **Scalability:** Allows scaling individual services based on demand.
*   **Independent Deployment:** Facilitates faster development cycles and independent deployments.
*   **Fault Isolation:** Failure in one service does not necessarily affect other services.
*   **Technology Diversity:** Enables using different technologies for different services based on their specific needs.

**Key Components:**

*   **API Gateway:** Acts as a single entry point for all client requests, routing them to the appropriate microservices. We'll utilize an API Gateway solution like Kong or Tyk.
*   **Data Ingestion Service:** Responsible for collecting and processing land/property data from various sources (e.g., government databases, real estate portals).
*   **Analysis Service:** Performs statistical analysis and calculations on the land/property data to generate insights (e.g., price trends, investment potential).
*   **Visualization Service:** Creates interactive maps, charts, and graphs to visually represent the analyzed data.
*   **User Management Service:** Handles user authentication, authorization, and profile management.
*   **Notification Service:** Responsible for sending notifications to users based on their preferences and alerts.

**Communication:**

Microservices will communicate with each other using asynchronous messaging (e.g., RabbitMQ, Kafka) for non-critical operations and synchronous REST APIs for request/response scenarios.

### 2. Data Models

The core data model revolves around the concept of a "Land Parcel" (Arsa).  Here's a simplified representation:

```json
{
  "parcel_id": "UUID",
  "location": {
    "latitude": "float",
    "longitude": "float",
    "address": "string",
    "district": "string",
    "province": "string"
  },
  "area": {
    "size_sqm": "float",
    "unit": "string" // "sqm", "acre"
  },
  "ownership": {
    "owner_id": "UUID", // Reference to User Management Service
    "ownership_type": "string" // "private", "public"
  },
  "legal_status": {
    "title_deed": "string",
    "zoning": "string", // Zoning codes
    "restrictions": "array" // List of restrictions
  },
  "market_data": {
    "estimated_value": "float",
    "last_sale_price": "float",
    "price_history": [
      {
        "date": "date",
        "price": "float"
      }
    ]
  },
  "features": {
    "land_type": "string", // "agricultural", "residential", "commercial"
    "terrain": "string",
    "accessibility": "string"
  }
}
```

**Explanation:**

*   **parcel_id:** Unique identifier for each land parcel.
*   **location:**  Geographic coordinates and address information.
*   **area:** Size of the land parcel.
*   **ownership:**  Information about the owner and ownership type.
*   **legal_status:**  Details regarding the title deed, zoning, and any restrictions.
*   **market_data:**  Data related to the market value and sales history of the parcel.
*   **features:**  Characteristics of the land parcel.

Each microservice will likely maintain its own database tailored to its specific data needs.  For example, the Analysis Service might store pre-calculated statistical data related to land parcels.

### 3. API Definitions

We will use RESTful APIs for inter-service communication and for the client application to interact with the backend.  API definitions will be documented using OpenAPI (Swagger) specification.

**Example API (Data Ingestion Service):**

*   **Endpoint:** `/api/v1/parcels`
*   **Method:** `POST`
*   **Description:** Creates a new land parcel.
*   **Request Body:** JSON representation of the `Land Parcel` data model.
*   **Response:**
    *   `201 Created`:  Successful creation. Returns the `parcel_id` in the response body.
    *   `400 Bad Request`:  Invalid request data.
    *   `500 Internal Server Error`:  Server error.

*   **Endpoint:** `/api/v1/parcels/{parcel_id}`
*   **Method:** `GET`
*   **Description:** Retrieves a land parcel by its ID.
*   **Response:**
    *   `200 OK`:  Successful retrieval. Returns the JSON representation of the `Land Parcel`.
    *   `404 Not Found`:  Parcel not found.
    *   `500 Internal Server Error`:  Server error.

*   **Endpoint:** `/api/v1/parcels/{parcel_id}`
*   **Method:** `PUT`
*   **Description:** Updates an existing land parcel.
*   **Request Body:** JSON representation of the updated `Land Parcel` data model.
*   **Response:**
    *   `200 OK`:  Successful update.
    *   `404 Not Found`:  Parcel not found.
    *   `400 Bad Request`: Invalid request data.
    *   `500 Internal Server Error`:  Server error.

Similar APIs will be defined for other services, such as the Analysis Service (e.g., `/api/v1/analysis/parcel/{parcel_id}/trends`) and the Visualization Service (e.g., `/api/v1/visualization/parcel/{parcel_id}/map`).

### 4. Component Structure

Each microservice will be structured using a layered architecture:

*   **Presentation Layer (API Layer):** Handles incoming requests and responses.
*   **Business Logic Layer:** Implements the core business logic of the service.
*   **Data Access Layer:**  Provides access to the underlying database or data source.
*   **Utilities/Helpers:**  Reusable components and functions.

**Example (Analysis Service):**

```
analysis-service/
├── api/
│   ├── controllers/
│   │   └── analysis_controller.py
│   ├── routes/
│   │   └── analysis_routes.py
├── business_logic/
│   └── analysis_engine.py
├── data_access/
│   └── parcel_repository.py
├── utils/
│   └── helper_functions.py
├── models/
│   └── parcel_model.py
└── app.py (Main application entry point)
```

### 5. Integration Points

*   **Data Sources:** Integration with various data sources, including government databases (e.g., land registry), real estate portals, and potentially user-uploaded data.  Data ingestion pipelines will be built to handle different data formats and sources.
*   **Mapping Services:** Integration with mapping services like Google Maps, Leaflet, or Mapbox for displaying land parcels on maps.
*   **Authentication Provider:** Integration with an authentication provider (e.g., Auth0, Okta) for user authentication and authorization.
*   **Messaging Queue (RabbitMQ/Kafka):**  Used for asynchronous communication between microservices.
*   **Database:** Each microservice will connect to its respective database (e.g., PostgreSQL, MongoDB).
*   **API Gateway:** All requests will be routed through the API Gateway.

### 6. Scalability Strategy

*   **Horizontal Scaling:** Microservices can be scaled horizontally by deploying multiple instances of each service behind a load balancer.
*   **Database Scaling:** The database for each microservice can be scaled independently using techniques like read replicas, sharding, or database clustering.
*   **Caching:** Implement caching mechanisms (e.g., Redis, Memcached) to reduce database load and improve response times.
*   **Asynchronous Processing:** Utilize message queues for handling long-running or resource-intensive tasks asynchronously.
*   **Containerization (Docker):**  Using Docker allows for easy deployment and scaling of microservices.
*   **Orchestration (Kubernetes):** Kubernetes will be used to manage and orchestrate the microservices, enabling automated deployments, scaling, and fault tolerance.

Created on 13.05.2025
```