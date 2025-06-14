# Management Backend 

## Overview
The Log-Interaction Management Backend is built using FastAPI and serves as the backend for the ai-agent based interaction management system. It provides a set of RESTful API endpoints to manage interactions with healthcare professionals (HCPs), including creating, updating, deleting, and fetching interaction records. The backend also handles CORS for the frontend application and initializes a MySQL database connection.

##Dynamically fill as per prompt agentic - groq Ai

## Features
- RESTful API for managing HCP interactions
- CORS middleware for secure communication with the frontend
- MySQL database integration for persistent data storage
- Tools for logging and managing interactions

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- MySQL server
- Required Python packages (listed in `requirements.txt`)

### Installation
1. Clone the repository:
 

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your MySQL database:
   - Create a database named `patient_db`.
   - Update the database connection details in `main.py` if necessary.

5. Run the FastAPI application:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Create Interaction
- **Endpoint:** `POST /interactions`
- **Description:** Logs a new interaction with an HCP.
- **Request Body:** JSON object containing interaction details.

### Update Interaction
- **Endpoint:** `PUT /interactions/{interaction_id}`
- **Description:** Updates an existing interaction by ID.
- **Request Body:** JSON object containing updated interaction details.

### Delete Interaction
- **Endpoint:** `DELETE /interactions/{interaction_id}`
- **Description:** Deletes an interaction by ID.

### Fetch Interactions
- **Endpoint:** `GET /interactions`
- **Description:** Retrieves a list of all interactions.


1. POST /chat

- Accepts a chat message and optional form data, processes it through the AI workflow, and returns an AI-generated response plus updated form data.
- Request body: JSON object with at least a "text" field, and optionally any of the form fields.


2. GET /interactions

- Returns a list of all HCP interactions in the database.
- Response: JSON array of Interaction objects, each with fields:
  - id, hcp_id, interaction_type, date, time, attendees, topic_discussed,
    materials_shared, hcp_sentiment, outcomes, follow_up_action, summary, outcome



## Usage Examples
- To create a new interaction, send a POST request to `/interactions` with the required data.
- To update an interaction, send a PUT request to `/interactions/{interaction_id}` with the updated data.
- To delete an interaction, send a DELETE request to `/interactions/{interaction_id}`.
- To fetch all interactions, send a GET request to `/interactions`.

## License
This project is licensed under the MIT License. See the LICENSE file for details.









# frontend part Application

## Overview
The Patient Management Application is a comprehensive system designed to facilitate the management of healthcare provider (HCP) interactions. It consists of a backend built with FastAPI and a frontend developed using React. This application allows users to log, edit, delete, and fetch interactions with healthcare providers efficiently.

## Frontend Setup

### Prerequisites
- Node.js (version 14 or higher)
- npm (Node Package Manager)

### Installation
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install the required dependencies:
   ```
   npm install
   ```

### Running the Application
To start the React application, run the following command:
```
npm start
```
This will start the development server and open the application in your default web browser at `http://localhost:5173`.

## Component Description
- **App.jsx**: The main component of the application that manages the state for chat messages and interactions. It handles form submissions and integrates with the backend API to fetch and manage interactions.

## Usage
Once the application is running, you can interact with the user interface to log new interactions, edit existing ones, and delete interactions as needed. The application communicates with the backend API to perform these operations.

## Links
- [Backend Documentation](../backend/README.md)
- [Frontend Documentation](./README.md)

## Contributing
Contributions to the Patient Management Application are welcome! Please fork the repository and submit a pull request for any changes or enhancements.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
