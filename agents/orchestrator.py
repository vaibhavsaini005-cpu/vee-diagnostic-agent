import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def load_failures():
    with open("data/failures.json", "r") as f:
        return json.load(f)

def diagnose_company(company_input: str) -> str:
    failures = load_failures()
    failures_text = json.dumps(failures, indent=2)
    
    prompt = f"""
You are the Vee Group Diagnostic AI — the world's most advanced company failure prevention system.

You have access to a database of {len(failures)} failed companies representing billions in lost capital.

FAILURE DATABASE:
{failures_text}

COMPANY TO DIAGNOSE:
{company_input}

Your job is to:
1. PATTERN MATCHER: Find the 2-3 closest matching failure patterns from the database
2. RISK ANALYSER: Score this company risk in each category: Growth, Brand, UX, Campaign 0-100%
3. REPORT GENERATOR: Write a clear diagnostic report with specific actions

Format your response exactly like this:

## PATTERN MATCHES
[List the matching companies and why they match]

## RISK SCORES
- Growth Risk: X%
- Brand Risk: X%
- UX Risk: X%
- Campaign Risk: X%
- Overall Failure Risk: X%

## DIAGNOSTIC REPORT
[Plain language explanation of the biggest threats]

## IMMEDIATE ACTIONS
[5 specific things to do in the next 30 days]

## SURVIVAL PROBABILITY WITH VEE GROUP INTERVENTION
X%
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    return response.text

if __name__ == "__main__":
    print("VEE GROUP — Company Failure Diagnostic System")
    print("=" * 50)
    print("Describe your company and we will diagnose your failure risk.")
    print()
    
    company_input = input("Tell us about your company: ")
    
    print("\nAnalysing against failure database...\n")
    result = diagnose_company(company_input)
    print(result)
