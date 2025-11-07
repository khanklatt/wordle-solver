"""
FastAPI HTTP API for Wordle Solver MCP Tool

Requirement 6.5: Expose HTTP API endpoint via FastAPI
Requirement 6.5.1: POST endpoint at /process_feedback with JSON request body
Requirement 6.5.2: Return JSON response with candidates and suggestions
Requirement 6.5.3: Runnable as standalone server for MCP tool infrastructure

This module provides an HTTP API interface to the Wordle Solver, enabling
remote access via standard REST API for MCP tools that communicate over HTTP.
"""
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path to import wordle_solver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from wordle_solver import WordleSolver

# Create FastAPI application
app = FastAPI(
    title="Wordle Solver API",
    description="HTTP API for Wordle Solver MCP Tool - Helps solve Wordle puzzles by analyzing letter frequencies and filtering candidate words",
    version="1.0.0",
    servers=[
        {"url": "http://localhost:8000", "description": "Local development server"},
    ]
)

# Create a single solver instance to reuse across requests
solver = WordleSolver()


class ProcessFeedbackRequest(BaseModel):
    """
    Request model for /process_feedback endpoint
    
    Requirement 6.5.1: Accept JSON request body with guess, greens, yellows, greys
    """
    guess: str = Field(..., description="The guessed word (e.g., 'saint')")
    greens: str = Field(..., description="Green letters feedback string with dots (e.g., '..i..')")
    yellows: str = Field(..., description="Yellow letters feedback string with dots (e.g., 's....')")
    greys: List[str] = Field(..., description="List of excluded letters (e.g., ['a', 'n', 't'])")
    
    class Config:
        json_schema_extra = {
            "example": {
                "guess": "saint",
                "greens": "..i..",
                "yellows": "s....",
                "greys": ["a", "n", "t"]
            }
        }


class Suggestion(BaseModel):
    """Suggestion model with word and score"""
    word: str = Field(..., description="Suggested word")
    score: int = Field(..., description="Word score (lower is better)")


class ProcessFeedbackResponse(BaseModel):
    """
    Response model for /process_feedback endpoint
    
    Requirement 6.5.2: Return JSON response with candidates and suggestions
    """
    candidates: List[str] = Field(..., description="List of candidate words")
    suggestions: List[Suggestion] = Field(..., description="List of suggested words with scores")
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidates": ["guise", "poise", "noise"],
                "suggestions": [
                    {"word": "GUISE", "score": 19},
                    {"word": "POISE", "score": 20}
                ]
            }
        }


@app.post("/process_feedback", response_model=ProcessFeedbackResponse)
async def process_feedback(request: ProcessFeedbackRequest) -> ProcessFeedbackResponse:
    """
    Process Wordle feedback and return candidates and suggestions
    
    Requirement 6.5: Expose HTTP API endpoint via FastAPI
    Requirement 6.5.1: POST endpoint at /process_feedback with JSON request body
    Requirement 6.5.2: Return JSON response with candidates and suggestions
    
    Args:
        request: ProcessFeedbackRequest containing guess, greens, yellows, greys
    
    Returns:
        ProcessFeedbackResponse containing candidates and suggestions
    
    Raises:
        HTTPException: If processing fails or input is invalid
    """
    try:
        # Call the solver's process_feedback method
        result = solver.process_feedback(
            guess=request.guess,
            greens=request.greens,
            yellows=request.yellows,
            greys=request.greys
        )
        
        # Convert suggestions to Suggestion models
        suggestions = [
            Suggestion(word=s["word"], score=s["score"])
            for s in result["suggestions"]
        ]
        
        # Return response
        return ProcessFeedbackResponse(
            candidates=result["candidates"],
            suggestions=suggestions
        )
    
    except Exception as e:
        # Handle any errors gracefully
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feedback: {str(e)}"
        )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    
    Returns:
        Status indicating API is healthy
    """
    return {"status": "healthy", "service": "wordle-solver-api"}


@app.get("/.well-known/ai-plugin.json")
async def get_ai_plugin_json() -> JSONResponse:
    """
    Serve ChatGPT plugin manifest file
    
    Requirement 6.6: Support for ChatGPT plugins via ai-plugin.json
    
    Returns:
        ChatGPT plugin manifest JSON
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plugin_file = os.path.join(project_root, ".well-known", "ai-plugin.json")
    
    if os.path.exists(plugin_file):
        import json
        with open(plugin_file, 'r') as f:
            plugin_data = json.load(f)
        return JSONResponse(content=plugin_data)
    else:
        raise HTTPException(status_code=404, detail="Plugin manifest not found")


@app.get("/openapi.yaml")
async def get_openapi_yaml() -> Response:
    """
    Serve OpenAPI specification in YAML format
    
    Requirement 6.6: Support for ChatGPT plugins via openapi.yaml
    
    Returns:
        OpenAPI specification file in YAML format
    """
    import os
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    openapi_file = os.path.join(project_root, "openapi.yaml")
    
    if os.path.exists(openapi_file):
        return FileResponse(openapi_file, media_type="text/yaml")
    else:
        # Generate OpenAPI schema from FastAPI app
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Convert to YAML format
        try:
            import yaml
            yaml_content = yaml.dump(openapi_schema, default_flow_style=False, sort_keys=False, allow_unicode=True)
            return Response(content=yaml_content, media_type="text/yaml")
        except ImportError:
            # If yaml not available, return JSON (ChatGPT can handle JSON OpenAPI specs)
            import json
            json_content = json.dumps(openapi_schema, indent=2)
            return Response(content=json_content, media_type="application/json")


if __name__ == "__main__":
    """
    Requirement 6.5.3: Runnable as standalone server
    
    Run with: python -m uvicorn mcp.api:app --host 0.0.0.0 --port 8000
    Or: python mcp/api.py (if uvicorn is available)
    """
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("Error: uvicorn is required to run the server.")
        print("Install with: pip install uvicorn fastapi")
        sys.exit(1)
