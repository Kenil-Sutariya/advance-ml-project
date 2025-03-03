import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import re

# Academic Cloud API details
API_ENDPOINT = "https://chat-ai.academiccloud.de/v1/chat/completions" 
API_KEY = "api_key"  # Replace with your actual API key
MODEL_NAME = "meta-llama-3.1-8b-instruct" 

# Function to generate SPARQL query using Academic Cloud API
def generate_sparql_query(question):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = """
    You are a helpful assistant that generates SPARQL queries for DBpedia. Given a question, you will generate a valid SPARQL query to retrieve the answer from DBpedia.

    Here are some examples:

    ---

    Example 1:
    Question: What is the capital of France?
    SPARQL Query:
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>

    SELECT ?capital
    WHERE {
      <http://dbpedia.org/resource/France> dbo:capital ?capital .
    }

    ---

    Example 2:
    Question: What is the population of India?
    SPARQL Query:
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT ?population
    WHERE {
      <http://dbpedia.org/resource/India> dbo:populationTotal ?population .
    }

    ---

    Example 3:
    Question: Who is the CEO of Tesla?
    SPARQL Query:
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>

    SELECT ?ceo
    WHERE {
      <http://dbpedia.org/resource/Tesla,_Inc.> dbo:ceo ?ceo .
    }

    ---

    Now, generate a SPARQL query for the following question:
    Question: {USER_QUESTION}
    """.replace("{USER_QUESTION}", question)
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates SPARQL queries for DBpedia."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        llm_output = result["choices"][0]["message"]["content"].strip()
        
        # Extract SPARQL query from the LLM's response
        sparql_query = extract_sparql_query(llm_output)
        if sparql_query:
            return sparql_query
        else:
            print("Error: Failed to extract SPARQL query from the response.")
            return None
    except Exception as e:
        print(f"Error generating SPARQL query: {e}")
        return None

# Function to extract SPARQL query from the LLM's response
def extract_sparql_query(llm_output):
    # Try to extract query from markdown code blocks
    sparql_query = re.search(r"```sparql(.*?)```", llm_output, re.DOTALL)
    if sparql_query:
        return sparql_query.group(1).strip()
    
    # If no code block is found, try to extract the query directly
    sparql_query = re.search(r"(PREFIX.*?WHERE\s*\{.*?\})", llm_output, re.DOTALL)
    if sparql_query:
        return sparql_query.group(0).strip()
    
    # If no query is found, return None
    return None

# Function to query DBpedia using SPARQL
def query_dbpedia(sparql_query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"Error querying DBpedia: {e}")
        return None

# Function to process and display results
def process_results(results):
    if results and "results" in results and "bindings" in results["results"]:
        for result in results["results"]["bindings"]:
            for key, value in result.items():
                print(f"Answer: {value['value']}")
    else:
        print("Error: No results found.")

# Main function
def main():
    
    question = input("Enter your question: ")
    print(f"Question: {question}")
    
    sparql_query = generate_sparql_query(question)
    if not sparql_query:
        return
    
    print(f"SPARQL Query:\n{sparql_query}\n")

    results = query_dbpedia(sparql_query)
    if not results:
        return
    
    process_results(results)

if __name__ == "__main__":
    main()