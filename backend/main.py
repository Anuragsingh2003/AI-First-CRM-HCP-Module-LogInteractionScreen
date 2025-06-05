import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from groq import Groq
import aiomysql
from typing import List, Dict, Any
import os
from datetime import datetime
import re
import uuid

app = FastAPI(title="HCP CRM API")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY", "gsk_xEHmkwiawRQtLWGdyb3FYbBi8lqaJCF1tqVLf9uga21dd"),
    http_client=None
)

# Database pool
pool = None

async def init_db():
    """Initialize MySQL connection pool and create tables."""
    global pool
    pool = await aiomysql.create_pool(
        host="localhost", port=3306, user="root", password="", db="patient_db",
        autocommit=True, minsize=1, maxsize=10
    )
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS hcp_interactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    hcp_id VARCHAR(36) NOT NULL,
                    interaction_type VARCHAR(50),
                    date DATE,
                    time TIME,
                    attendees TEXT,
                    topic_discussed TEXT,
                    materials_shared TEXT,
                    hcp_sentiment VARCHAR(20),
                    outcomes TEXT,
                    follow_up_action TEXT,
                    summary TEXT,
                    outcome VARCHAR(50)
                )
            """)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS hcp_profiles (
                    hcp_id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(100),
                    specialty VARCHAR(100)
                )
            """)
            await conn.commit()

@tool
async def log_interaction(
    hcp_id: str,
    interaction_type: str = None,
    date: str = None,
    time: str = None,
    attendees: str = None,
    topic_discussed: str = None,
    materials_shared: str = None,
    hcp_sentiment: str = None,
    outcomes: str = None,
    follow_up_action: str = None
) -> Dict[str, Any]:
    """Log an HCP interaction with summarization and outcome classification."""
    try:
        # Validate date and time if provided
        date_obj = datetime.strptime(date, '%Y-%m-%d').date() if date else None
        time_obj = datetime.strptime(time, '%H:%M:%S').time() if time else None
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Validate HCP exists
                await cursor.execute("SELECT hcp_id, name FROM hcp_profiles WHERE hcp_id = %s", (hcp_id,))
                hcp = await cursor.fetchone()
                if not hcp:
                    return {"error": f"HCP ID {hcp_id} not found"}
                # Summarize notes (topic_discussed as notes)
                notes = topic_discussed or ""
                summary = ""
                outcome = ""
                if notes:
                    # Use a more analytical prompt for summary
                    response = groq_client.chat.completions.create(
                        model="gemma2-9b-it",
                        messages=[{
                            "role": "user",
                            "content": (
                                "Analyze the following meeting notes and provide a concise, factual summary. "
                                "Focus on key discussion points, decisions made, concerns raised, and any action items. "
                                "Avoid generic or instructional responses. Notes:\n" + interaction_type + notes + topic_discussed
                            )
                        }]
                    )
                    summary = response.choices[0].message.content.strip()
                    # Classify outcome
                    outcome_response = groq_client.chat.completions.create(
                        model="gemma2-9b-it",
                        messages=[{
                            "role": "user",
                            "content": (
                                "Based on these notes, classify the outcome as 'interested', 'not interested', or 'follow-up needed'. "
                                "Only return one of these three labels. Notes:\n" + notes 
                            )
                        }]
                    )
                    outcome = outcome_response.choices[0].message.content.strip()
                    # Truncate outcome to fit the VARCHAR(50) column
                    outcome = outcome[:50]
                await cursor.execute(
                    """
                    INSERT INTO hcp_interactions (
                        hcp_id, interaction_type, date, time, attendees, topic_discussed,
                        materials_shared, hcp_sentiment, outcomes, follow_up_action, summary, outcome
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (hcp_id, interaction_type, date_obj, time_obj, attendees, topic_discussed,
                     materials_shared, hcp_sentiment, outcomes, follow_up_action, summary, outcome)
                )
                await conn.commit()
                return {
                    "id": cursor.lastrowid,
                    "hcp_id": hcp_id,
                    "interaction_type": interaction_type,
                    "date": date,
                    "time": time,
                    "attendees": attendees,
                    "topic_discussed": topic_discussed,
                    "materials_shared": materials_shared,
                    "hcp_sentiment": hcp_sentiment,
                    "outcomes": outcomes,
                    "follow_up_action": follow_up_action,
                    "summary": summary,
                    "outcome": outcome
                }
    except ValueError as e:
        return {"error": f"Invalid date or time format: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

@tool
async def edit_interaction(
    interaction_id: int,
    hcp_id: str,
    interaction_type: str = None,
    date: str = None,
    time: str = None,
    attendees: str = None,
    topic_discussed: str = None,
    materials_shared: str = None,
    hcp_sentiment: str = None,
    outcomes: str = None,
    follow_up_action: str = None
) -> Dict[str, Any]:
    """Edit an existing HCP interaction with updated summarization and outcome."""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date() if date else None
        time_obj = datetime.strptime(time, '%H:%M:%S').time() if time else None
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT hcp_id FROM hcp_profiles WHERE hcp_id = %s", (hcp_id,))
                if not await cursor.fetchone():
                    return {"error": f"HCP ID {hcp_id} not found"}
                notes = topic_discussed or ""
                summary = ""
                outcome = ""
                if notes:
                    response = groq_client.chat.completions.create(
                        model="gemma2-9b-it",
                        messages=[{"role": "user", "content": f"Summarize: {notes}"}]
                    )
                    summary = response.choices[0].message.content
                    outcome_response = groq_client.chat.completions.create(
                        model="gemma2-9b-it",
                        messages=[{"role": "user", "content": f"Classify outcome: {notes}"}]
                    )
                    outcome = outcome_response.choices[0].message.content
                    # Truncate outcome to fit the VARCHAR(50) column
                    outcome = outcome[:50]
                await cursor.execute(
                    """
                    UPDATE hcp_interactions SET
                        hcp_id = %s, interaction_type = %s, date = %s, time = %s, attendees = %s,
                        topic_discussed = %s, materials_shared = %s, hcp_sentiment = %s,
                        outcomes = %s, follow_up_action = %s, summary = %s, outcome = %s
                    WHERE id = %s
                    """,
                    (hcp_id, interaction_type, date_obj, time_obj, attendees, topic_discussed,
                     materials_shared, hcp_sentiment, outcomes, follow_up_action, summary, outcome, interaction_id)
                )
                await conn.commit()
                if cursor.rowcount == 0:
                    return {"error": "Interaction not found"}
                return {
                    "id": interaction_id,
                    "hcp_id": hcp_id,
                    "interaction_type": interaction_type,
                    "date": date,
                    "time": time,
                    "attendees": attendees,
                    "topic_discussed": topic_discussed,
                    "materials_shared": materials_shared,
                    "hcp_sentiment": hcp_sentiment,
                    "outcomes": outcomes,
                    "follow_up_action": follow_up_action,
                    "summary": summary,
                    "outcome": outcome
                }
    except ValueError as e:
        return {"error": f"Invalid date or time format: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

@tool
async def delete_interaction(interaction_id: int) -> Dict[str, Any]:
    """Delete an HCP interaction by ID."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM hcp_interactions WHERE id = %s", (interaction_id,))
                await conn.commit()
                if cursor.rowcount == 0:
                    return {"error": "Interaction not found"}
                return {"success": f"Interaction {interaction_id} deleted"}
    except Exception as e:
        return {"error": str(e)}

@tool
async def validate_or_create_hcp(hcp_name: str = None, hcp_id: str = None, specialty: str = None) -> Dict[str, Any]:
    """Validate an HCP ID or create/update an HCP profile."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if hcp_id:
                    await cursor.execute("SELECT hcp_id, name, specialty FROM hcp_profiles WHERE hcp_id = %s", (hcp_id,))
                    row = await cursor.fetchone()
                    if row:
                        # Update if new details provided
                        if specialty and specialty != row[2]:
                            await cursor.execute(
                                "UPDATE hcp_profiles SET specialty = %s WHERE hcp_id = %s",
                                (specialty, hcp_id)
                            )
                            await conn.commit()
                        return {"hcp_id": row[0], "name": row[1], "specialty": specialty or row[2]}
                if hcp_name:
                    # Check if HCP exists by name
                    await cursor.execute("SELECT hcp_id, name, specialty FROM hcp_profiles WHERE name = %s", (hcp_name,))
                    row = await cursor.fetchone()
                    if row:
                        # Update if new details provided
                        if specialty and specialty != row[2]:
                            await cursor.execute(
                                "UPDATE hcp_profiles SET specialty = %s WHERE hcp_id = %s",
                                (specialty, row[0])
                            )
                            await conn.commit()
                        return {"hcp_id": row[0], "name": row[1], "specialty": specialty or row[2]}
                    # Create new HCP
                    new_hcp_id = str(uuid.uuid4())
                    await cursor.execute(
                        "INSERT INTO hcp_profiles (hcp_id, name, specialty) VALUES (%s, %s, %s)",
                        (new_hcp_id, hcp_name, specialty)
                    )
                    await conn.commit()
                    return {"hcp_id": new_hcp_id, "name": hcp_name, "specialty": specialty}
                return {"error": "HCP name or ID required"}
    except Exception as e:
        return {"error": str(e)}

@tool
async def fetch_latest_interaction(hcp_id: str) -> Dict[str, Any]:
    """Fetch the latest interaction for a given HCP ID."""
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT id, hcp_id, interaction_type, date, time, attendees, topic_discussed,
                           materials_shared, hcp_sentiment, outcomes, follow_up_action, summary, outcome
                    FROM hcp_interactions
                    WHERE hcp_id = %s
                    ORDER BY date DESC, time DESC
                    LIMIT 1
                    """,
                    (hcp_id,)
                )
                row = await cursor.fetchone()
                if not row:
                    return {"error": f"No interactions found for HCP ID {hcp_id}"}
                return {
                    "interaction_id": row[0],
                    "hcp_id": row[1],
                    "interaction_type": row[2],
                    "date": row[3].strftime('%Y-%m-%d') if row[3] else None,
                    "time": (
                        f"{row[4].seconds//3600:02}:{(row[4].seconds//60)%60:02}:{row[4].seconds%60:02}"
                        if row[4] else None
                    ),
                    "attendees": row[5],
                    "topic_discussed": row[6],
                    "materials_shared": row[7],
                    "hcp_sentiment": row[8],
                    "outcomes": row[9],
                    "follow_up_action": row[10],
                    "summary": row[11],
                    "outcome": row[12]
                }
    except Exception as e:
        return {"error": str(e)}

@tool
async def get_product_info(product_name: str) -> Dict[str, Any]:
    """Retrieve product information for reference during interactions."""
    return {"product_name": product_name, "details": "Info about product"}

@tool
async def classify_outcome(notes: str) -> Dict[str, Any]:
    """Classify the outcome of an interaction based on notes."""
    try:
        response = groq_client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "user", "content": f"Classify outcome as 'interested', 'not interested', or 'follow-up needed': {notes}"}]
        )
        return {"outcome": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

@tool
async def extract_entities(text: str) -> Dict[str, Any]:
    """Extract entities from chat input."""
    try:
        # Detect fetch/retrieve/update command
        fetch_command_match = re.search(r'\b(retrieve|fetch|update|replace)\b', text, re.IGNORECASE)
        is_fetch_command = bool(fetch_command_match)
        command = fetch_command_match.group(0).lower() if fetch_command_match else None

        # Extract HCP name for fetch commands (e.g., "retrieve dr.davis")
        hcp_name_for_fetch_match = re.search(r'(?:retrieve|fetch|update|replace)\s+dr\.?\s*(\w+)', text, re.IGNORECASE)
        hcp_name_for_fetch = hcp_name_for_fetch_match.group(1).strip() if hcp_name_for_fetch_match else None

        # Extract field to update (e.g., "HCP Sentiment to positive")
        update_field_match = re.search(r'(HCP\s+Specialty|HCP\s+Sentiment|interaction\s+type|date|time|meeting|attendees|topic|materials|outcomes|follow-up|follow-up\s+action)\s+to\s+(.+?)(?:$|\s+and\s+|$)', text, re.IGNORECASE)
        update_field = None
        update_value = None
        if update_field_match:
            field_name = update_field_match.group(1).lower().replace(" ", "_")
            update_value = update_field_match.group(2).strip()
            # Map field name to state key
            field_mapping = {
                "hcp_specialty": "specialty",
                "hcp_sentiment": "hcp_sentiment",
                "interaction_type": "interaction_type",
                "date": "date",
                "time": "time",
                "meeting": "meeting",
                "attendees": "attendees",
                "topic": "topic_discussed",
                "materials": "materials_shared",
                "outcomes": "outcomes",
                "follow_up": "follow_up_action",
                "follow_up_action": "follow_up_action"
            }
            update_field = field_mapping.get(field_name)

        # Extract HCP name for "met" commands (e.g., "met dr.davis")
        hcp_name_match = re.search(r'(?:met)\s+dr\.?\s*(\w+)', text, re.IGNORECASE)
        hcp_name = hcp_name_match.group(1).strip() if hcp_name_match else hcp_name_for_fetch

        # Extract HCP ID (e.g., "HCP 123")
        hcp_id_match = re.search(r'HCP\s*(\d+)', text, re.IGNORECASE)
        hcp_id = hcp_id_match.group(1) if hcp_id_match else None

        # Extract specialty (e.g., "specialty: cardiologist")
        specialty_match = re.search(r'(?:specialty|HCP Specialty):\s*(\w+)', text, re.IGNORECASE)
        specialty = specialty_match.group(1).strip() if specialty_match else None

        # Validate or create HCP
        hcp_result = await validate_or_create_hcp.ainvoke({"hcp_name": hcp_name, "hcp_id": hcp_id, "specialty": specialty})
        if "error" in hcp_result:
            return {"error": hcp_id}

        hcp_id = hcp_result["hcp_id"]
        hcp_name = hcp_result["name"]
        hcp_specialty = hcp_result.get("outcomes", "")

        # Extract interaction type (e.g., "call")
        interaction_type_match = re.search(r'\b(meeting|call|email|attendance)\b', text, re.IGNORECASE)
        interaction_type = interaction_type_match.group(0) if interaction_type_match else "meeting"

        # Extract date
        # e.g., "2025-06-05" or "today"
        date_match_exact = re.search(r'\b(\d{4}-\d{2}-d{2})\b', text)
        date_match_today = re.search(r'\btoday\b', text, re.IGNORECASE)
        date = date_match_exact.group(1) if date_match_exact else datetime.now().strftime('%Y-%m-%d') if date_match_today else None

        # Extract time
        # e.g., "09:30")
        time_match = re.search(r'\b(\d{2}:\d{2}(?::\ d{2})?)\b', text)
        time = (time_match.group(1) + ":00" if time_match and len(time_match.group(1).split(":")) == 2 else time_match.group(1) if time_match else None)

        # Extract attendees
        attendees_match = re.search(r'attendees:\s*(.+?)(?:\s*(?:meeting|call|email|attendance|date|time|topic|material|material|sentiment| outcomes| outcomes| out|follow-up|$))', text, re.IGNORECASE)
        attendees = attendees_match.group(1).strip() if attendees_match else None

        # Extract topic discussed
        # e.g., "discussed product Z pricing")
        topic_match = re.search(r'(?:discussed|topic:)\s*(.+?)(?:\s*(?:meeting|call|attendance|date|time|attendees|material|sentiment| outcomes| outcomes| out|follow-up|$))', text, re.IGNORECASE)
        topic_discussed = topic_match.group(1).strip() if topic_match else None

        # Extract materials shared
        # e.g., "shared brochure")
        materials_match = re.search(r'(?:shared|material:):s*(.+?)(?:\s*(?:meeting| meeting|material|meeting| material|material| material| time|| out| out|follow-up|$))', text, re.IGNORECASE)
        materials_shared = materials_match.group(1).strip() if materials_match else None

        # Extract sentiment
        # e.g., "neutral sentiment" - only if not part of update command)
        sentiment_match = re.search(r'(positive|neutral|negative)\s*sentiment', text, re.IGNORECASE)
        hcp_sentiment = sentiment_match.group(1).lower() if sentiment_match and not update_field else None

        # Extract outcomes
        outcomes_match = re.search(r'outcomes:\s*(.+?)(?:\s*(?:meeting|call|email|attendance|date|time|attendees|topic|material|sentiment|follow-up|$))', text, re.IGNORECASE)
        outcomes = outcomes_match.group(1).strip() if outcomes_match else None

        # Extract follow-up action
        follow_up_match = re.search(r'(?:follow-up|follow up action:)\s*(.+?)(?:\s*(?:meeting|call|email|attendance|date|time|attendees|topic|material|sentiment|outcomes|$))', text, re.IGNORECASE)
        follow_up_action = follow_up_match.group(1).strip() if follow_up_match else None

        return {
            "is_fetch_command": is_fetch_command,
            "command": command,
            "update_field": update_field,
            "update_value": update_value,
            "hcp_id": hcp_id,
            "hcp_name": hcp_name,
            "specialty": hcp_specialty,
            "interaction_type": interaction_type,
            "date": date,
            "time": time,
            "attendees": attendees,
            "topic_discussed": topic_discussed,
            "materials_shared": materials_shared,
            "hcp_sentiment": hcp_sentiment,
            "outcomes": outcomes,
            "follow_up_action": follow_up_action
        }
    except Exception as e:
        return {"error": f"Failed to parse input: {str(e)}. Please use the format: 'retrieve dr.<name> HCP Sentiment to positive' or 'met dr.<name>, discussed <topic>, <sentiment> sentiment, shared <materials>'"}

# LangGraph State
class InteractionState(BaseModel):
    messages: List[Dict[str, str]]
    hcp_id: str = ""
    hcp_name: str = ""
    specialty: str = ""
    interaction_type: str = ""
    date: str = ""
    time: str = ""
    attendees: str = ""
    topic_discussed: str = ""
    materials_shared: str = ""
    hcp_sentiment: str = ""
    outcomes: str = ""
    follow_up_action: str = ""
    interaction_id: int = 0

# LangGraph Workflow
def create_workflow():
    workflow = StateGraph(InteractionState)
    
    async def process_interaction(state: InteractionState) -> InteractionState:
        last_message = state.messages[-1]["content"].lower()
        entities = await extract_entities.ainvoke(last_message)
        if "error" in entities:
            return InteractionState(messages=state.messages + [{"role": "assistant", "content": entities["error"]}])
        
        # Default values from extracted entities
        hcp_id = entities.get("hcp_id", state.hcp_id) or ""
        hcp_name = entities.get("hcp_name", state.hcp_name) or ""
        specialty = entities.get("specialty", state.specialty) or ""
        interaction_type = entities.get("interaction_type", state.interaction_type) or ""
        date = entities.get("date", state.date) or ""
        time = entities.get("time", state.time) or ""
        attendees = entities.get("attendees", state.attendees) or ""
        topic_discussed = entities.get("topic_discussed", state.topic_discussed) or ""
        materials_shared = entities.get("materials_shared", state.materials_shared) or ""
        hcp_sentiment = entities.get("hcp_sentiment", state.hcp_sentiment) or ""
        outcomes = entities.get("outcomes", state.outcomes) or ""
        follow_up_action = entities.get("follow_up_action", state.follow_up_action) or ""
        interaction_id = state.interaction_id

        # Handle fetch/retrieve/update commands
        if entities.get("is_fetch_command"):
            # Fetch the latest interaction for the HCP
            interaction_data = await fetch_latest_interaction.ainvoke(hcp_id)
            if "error" in interaction_data:
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": interaction_data["error"]}])
            
            # Update state with the latest interaction data
            interaction_id = interaction_data["interaction_id"]
            hcp_id = interaction_data["hcp_id"]
            interaction_type = interaction_data["interaction_type"] or ""
            date = interaction_data["date"] or ""
            time = interaction_data["time"] or ""
            attendees = interaction_data["attendees"] or ""
            topic_discussed = interaction_data["topic_discussed"] or ""
            materials_shared = interaction_data["materials_shared"] or ""
            hcp_sentiment = interaction_data["hcp_sentiment"] or ""
            outcomes = interaction_data["outcomes"] or ""
            follow_up_action = interaction_data["follow_up_action"] or ""

            # Apply the update if specified (e.g., "HCP Sentiment to positive")
            update_field = entities.get("update_field")
            update_value = entities.get("update_value")
            if update_field:
                if update_field == "hcp_sentiment":
                    hcp_sentiment = update_value.lower() if update_value.lower() in ["positive", "neutral", "negative"] else hcp_sentiment
                elif update_field == "interaction_type":
                    interaction_type = update_value.lower() if update_value.lower() in ["meeting", "call", "email", "visit"] else interaction_type
                elif update_field == "date":
                    try:
                        datetime.strptime(update_value, '%Y-%m-%d')
                        date = update_value
                    except ValueError:
                        date = date  # Keep existing date if invalid
                elif update_field == "time":
                    time = update_value + ":00" if len(update_value.split(":")) == 2 else update_value
                elif update_field == "attendees":
                    attendees = update_value
                elif update_field == "topic_discussed":
                    topic_discussed = update_value
                elif update_field == "materials_shared":
                    materials_shared = update_value
                elif update_field == "outcomes":
                    outcomes = update_value
                elif update_field == "follow_up_action":
                    follow_up_action = update_value
                elif update_field == "specialty":
                    specialty = update_value

            # Fill the form with the fetched (and possibly updated) data
            return InteractionState(
                messages=state.messages + [{"role": "assistant", "content": f"Form filled with latest interaction for {hcp_name}: HCP ID: {hcp_id}, Specialty: {specialty or 'Not specified'}, Interaction Type: {interaction_type or 'Not specified'}, Date: {date or 'Not specified'}, Time: {time or 'Not specified'}, Attendees: {attendees or 'Not specified'}, Topic: {topic_discussed or 'Not specified'}, Materials: {materials_shared or 'Not specified'}, Sentiment: {hcp_sentiment or 'Not specified'}, Outcomes: {outcomes or 'Not specified'}, Follow-Up: {follow_up_action or 'Not specified'}"}],
                hcp_id=hcp_id,
                hcp_name=hcp_name,
                specialty=specialty,
                interaction_type=interaction_type,
                date=date,
                time=time,
                attendees=attendees,
                topic_discussed=topic_discussed,
                materials_shared=materials_shared,
                hcp_sentiment=hcp_sentiment,
                outcomes=outcomes,
                follow_up_action=follow_up_action,
                interaction_id=interaction_id
            )

        # Existing logic for "met" or "fill form" commands
        if "fill form" in last_message or "met" in last_message:
            # Reset interaction_id for new interactions
            interaction_id = 0
            # Only fill the form, do not auto-save
            return InteractionState(
                messages=state.messages + [{"role": "assistant", "content": f"Form filled: HCP Name: {hcp_name}, HCP ID: {hcp_id}, Specialty: {specialty or 'Not specified'}, Interaction Type: {interaction_type}, Date: {date or 'Not specified'}, Time: {time or 'Not specified'}, Attendees: {attendees or 'Not specified'}, Topic: {topic_discussed or 'Not specified'}, Materials: {materials_shared or 'Not specified'}, Sentiment: {hcp_sentiment or 'Not specified'}, Outcomes: {outcomes or 'Not specified'}, Follow-Up: {follow_up_action or 'Not specified'}"}],
                hcp_id=hcp_id,
                hcp_name=hcp_name,
                specialty=specialty,
                interaction_type=interaction_type,
                date=date,
                time=time,
                attendees=attendees,
                topic_discussed=topic_discussed,
                materials_shared=materials_shared,
                hcp_sentiment=hcp_sentiment,
                outcomes=outcomes,
                follow_up_action=follow_up_action,
                interaction_id=interaction_id
            )
        elif "log interaction" in last_message or "save" in last_message:
            if not hcp_id:
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": "Please provide HCP name or ID to save."}])
            # Check if we're updating an existing interaction
            if interaction_id:
                result = await edit_interaction.ainvoke({
                    "interaction_id": interaction_id,
                    "hcp_id": hcp_id,
                    "interaction_type": interaction_type,
                    "date": date,
                    "time": time,
                    "attendees": attendees,
                    "topic_discussed": topic_discussed,
                    "materials_shared": materials_shared,
                    "hcp_sentiment": hcp_sentiment,
                    "outcomes": outcomes,
                    "follow_up_action": follow_up_action
                })
                if "error" in result:
                    return InteractionState(messages=state.messages + [{"role": "assistant", "content": result["error"]}])
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": f"Interaction updated: {str(result)}"}], **result)
            else:
                # Create a new interaction
                result = await log_interaction.ainvoke({
                    "hcp_id": hcp_id,
                    "interaction_type": interaction_type,
                    "date": date,
                    "time": time,
                    "attendees": attendees,
                    "topic_discussed": topic_discussed,
                    "materials_shared": materials_shared,
                    "hcp_sentiment": hcp_sentiment,
                    "outcomes": outcomes,
                    "follow_up_action": follow_up_action
                })
                if "error" in result:
                    return InteractionState(messages=state.messages + [{"role": "assistant", "content": result["error"]}])
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": f"Interaction created: {str(result)}"}], **result)
        elif "edit interaction" in last_message:
            if not (interaction_id and hcp_id):
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": "Please provide interaction ID and HCP name or ID to edit."}])
            result = await edit_interaction.ainvoke({
                "interaction_id": interaction_id,
                "hcp_id": hcp_id,
                "interaction_type": interaction_type,
                "date": date,
                "time": time,
                "attendees": attendees,
                "topic_discussed": topic_discussed,
                "materials_shared": materials_shared,
                "hcp_sentiment": hcp_sentiment,
                "outcomes": outcomes,
                "follow_up_action": follow_up_action
            })
            if "error" in result:
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": result["error"]}])
            return InteractionState(messages=state.messages + [{"role": "assistant", "content": str(result)}], **result)
        elif "delete interaction" in last_message:
            if not interaction_id:
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": "Please provide interaction ID to delete."}])
            result = await delete_interaction.ainvoke({"interaction_id": interaction_id})
            if "error" in result:
                return InteractionState(messages=state.messages + [{"role": "assistant", "content": result["error"]}])
            return InteractionState(messages=state.messages + [{"role": "assistant", "content": str(result)}])
        return InteractionState(messages=state.messages + [{"role": "assistant", "content": "I didn't understand your command. Try 'fill form', 'save', 'edit', or 'delete'."}])

    workflow.add_node("process_interaction", process_interaction)
    workflow.set_entry_point("process_interaction")
    workflow.add_edge("process_interaction", END)
    return workflow.compile()

graph = create_workflow()

# Pydantic Models
class InteractionCreate(BaseModel):
    hcp_id: str
    interaction_type: str | None = None
    date: str | None = None
    time: str | None = None
    attendees: str | None = None
    topic_discussed: str | None = None
    materials_shared: str | None = None
    hcp_sentiment: str | None = None
    outcomes: str | None = None
    follow_up_action: str | None = None

class Interaction(BaseModel):
    id: int
    hcp_id: str
    interaction_type: str | None
    date: str | None
    time: str | None
    attendees: str | None
    topic_discussed: str | None
    materials_shared: str | None
    hcp_sentiment: str | None
    outcomes: str | None
    follow_up_action: str | None
    summary: str | None
    outcome: str | None

# FastAPI Endpoints
@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/interactions", response_model=Interaction)
async def create_interaction(interaction: InteractionCreate):
    result = await log_interaction.ainvoke({
        "hcp_id": interaction.hcp_id,
        "interaction_type": interaction.interaction_type,
        "date": interaction.date,
        "time": interaction.time,
        "attendees": interaction.attendees,
        "topic_discussed": interaction.topic_discussed,
        "materials_shared": interaction.materials_shared,
        "hcp_sentiment": interaction.hcp_sentiment,
        "outcomes": interaction.outcomes,
        "follow_up_action": interaction.follow_up_action
    })
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.put("/interactions/{interaction_id}", response_model=Interaction)
async def update_interaction(interaction_id: int, interaction: InteractionCreate):
    result = await edit_interaction.ainvoke({
        "interaction_id": interaction_id,
        "hcp_id": interaction.hcp_id,
        "interaction_type": interaction.interaction_type,
        "date": interaction.date,
        "time": interaction.time,
        "attendees": interaction.attendees,
        "topic_discussed": interaction.topic_discussed,
        "materials_shared": interaction.materials_shared,
        "hcp_sentiment": interaction.hcp_sentiment,
        "outcomes": interaction.outcomes,
        "follow_up_action": interaction.follow_up_action
    })
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.delete("/interactions/{interaction_id}")
async def delete_interaction_endpoint(interaction_id: int):
    result = await delete_interaction.ainvoke({"interaction_id": interaction_id})
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/interactions", response_model=List[Interaction])
async def get_interactions():
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT id, hcp_id, interaction_type, date, time, attendees, topic_discussed,
                       materials_shared, hcp_sentiment, outcomes, follow_up_action, summary, outcome
                FROM hcp_interactions
            """)
            rows = await cursor.fetchall()
            return [
                Interaction(
                    id=row[0],
                    hcp_id=row[1],
                    interaction_type=row[2],
                    date=row[3].strftime('%Y-%m-%d') if row[3] else None,
                    time=(
                        f"{row[4].seconds//3600:02}:{(row[4].seconds//60)%60:02}:{row[4].seconds%60:02}"
                        if row[4] else None
                    ),
                    attendees=row[5],
                    topic_discussed=row[6],
                    materials_shared=row[7],
                    hcp_sentiment=row[8],
                    outcomes=row[9],
                    follow_up_action=row[10],
                    summary=row[11],
                    outcome=row[12]
                )
                for row in rows
            ]

@app.post("/chat")
async def chat_interaction(message: Dict[str, str]):
    state = InteractionState(
        messages=[{"role": "user", "content": message["text"]}],
        hcp_id=message.get("hcp_id", ""),
        hcp_name=message.get("hcp_name", ""),
        specialty=message.get("specialty", ""),
        interaction_type=message.get("interaction_type", ""),
        date=message.get("date", ""),
        time=message.get("time", ""),
        attendees=message.get("attendees", ""),
        topic_discussed=message.get("topic_discussed", ""),
        materials_shared=message.get("materials_shared", ""),
        hcp_sentiment=message.get("hcp_sentiment", ""),
        outcomes=message.get("outcomes", ""),
        follow_up_action=message.get("follow_up_action", ""),
        interaction_id=int(message.get("interaction_id", 0))
    )
    result_dict = await graph.ainvoke(state)
    result_state = InteractionState(**result_dict)
    return {
        "response": result_state.messages[-1]["content"],
        "form_data": {
            "hcp_id": result_state.hcp_id,
            "hcp_name": result_state.hcp_name,
            "specialty": result_state.specialty,
            "interaction_type": result_state.interaction_type,
            "date": result_state.date,
            "time": result_state.time,
            "attendees": result_state.attendees,
            "topic_discussed": result_state.topic_discussed,
            "materials_shared": result_state.materials_shared,
            "hcp_sentiment": result_state.hcp_sentiment,
            "outcomes": result_state.outcomes,
            "follow_up_action": result_state.follow_up_action,
            "interaction_id": result_state.interaction_id
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
