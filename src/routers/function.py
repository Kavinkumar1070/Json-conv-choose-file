import json
import re
import logging
from typing import Any, Dict
from datetime import datetime
from fastapi import WebSocket
import groq
from groq import Groq
from fastapi import WebSocket
import os 
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()
groq_api1 = os.getenv('GROQ_API_KEY1')
groq_api2 = os.getenv('GROQ_API_KEY2')
groq_api3 = os.getenv('GROQ_API_KEY3')

def choose_json(role):
    json_file = ['admin','employee','teamlead','onboard']                                                 
    for i in json_file:
        if i == role:
            return i +'.json'

def sanitize_json_string(response_text: str) -> str:
    # Remove any leading or trailing whitespace
    response_text = response_text.strip()
    # Match the JSON object in the response text
    json_match = re.search(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}', response_text, re.DOTALL)
    if json_match:
        json_string = json_match.group(0)
        # Remove any unnecessary escape characters (e.g., \_)
        json_string = re.sub(r'\\_', '_', json_string)
        try:
            # Validate and return formatted JSON
            parsed_json = json.loads(json_string)
            return json.dumps(parsed_json, indent=4)
        except json.JSONDecodeError:
            return "{}"
    return "{}"

async def get_project_details(websocket: WebSocket, query: str, jsonfile: str):
    projectinfo = {}
    try:
        with open(jsonfile, 'r') as f:
            json_config = json.load(f)
            project_names = json_config.keys()
            for i in project_names:
                if 'project description' in json_config[i]:
                    projectinfo[i] = json_config[i]['project description']
                else:
                    logging.warning(f"Warning: 'project description' missing for {i}")
    except FileNotFoundError:
        print("Error: The file was not found.")
        await websocket.send_text("Error: The configuration file was not found.")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file.")
        await websocket.send_text("Error: Failed to read the configuration file.")
        return None

    client = Groq(api_key=groq_api1)
    try:
        response = client.chat.completions.create(
            model='mixtral-8x7b-32768',
            messages=[
                {
            "role": "system",
            "content": f"""
            You are an AI assistant trained to extract project names based on project descriptions. Follow these steps:

            1. Correct any grammatical or spelling errors in the query.
            2. Review the provided project descriptions: {projectinfo}.
            3. Analyze the user query: "{query}" to determine which project name, if any, is referenced based on the descriptions.
            4. If a project name matches the query context, return that project name.
            5. If no project name matches or the query is unclear, return 'None'.
            6. The result should be a JSON object with the format shown below.

            Example:
            Query: "How do I update my project?"
            Project Titles and Descriptions: {projectinfo}
            Response:
            ~~~
            {{
                "project": "Project XYZ"
            }}
            ~~~

            Ensure the response is enclosed with `~~~` before and after the JSON output. Do not include any additional explanations.
            """
        },
                {
                    "role": "user",
                    "content": f"Extract the project name from the following query: {query} and Project Titles and Descriptions: {projectinfo}."
                }
            ]
        )
    except Exception as e:
        print(f"Error during API call: {e}")
        await websocket.send_text(e)        
        return "Internal server error"
    
    try:
        response_text = response.choices[0].message.content.strip()
        json_start_idx = response_text.find("~~~")
        json_end_idx = response_text.rfind("~~~") + 1
        result = response_text[json_start_idx:json_end_idx]
        result = sanitize_json_string(result)
        project_name = json.loads(result).get("project")
        
        if project_name == "None" or project_name is None:
            await websocket.send_text("You have asked for an irrelevant query. Ask anything from the listed projects:")
            user_input = await websocket.receive_text()
            user_input_data = json.loads(user_input)
            query = user_input_data.get("message")
            return await get_project_details(websocket, query, jsonfile)
        print("*****************************************************")
        print("project_name :",project_name)
        print("*****************************************************")
        return query, project_name

    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the response.")
        await websocket.send_text("Error: Failed to process the response.")
        return None
    except Exception as e:
        print(f"Error while processing the response: {e}")
        await websocket.send_text(e)
        return "Internal server error"

def get_project_script(project_name: str, jsonfile: str):
    try:
        with open(jsonfile, 'r') as f:
            json_config = json.load(f)
            project_script = json_config.get(project_name)
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("project_detail Done")
            print(project_script)
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
            return project_script
    
    except FileNotFoundError:
        print("Error: The file was not found.")
        return "Error: The configuration file was not found."
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from the file.")
        return "Error: Failed to read the configuration file."

def split_payload_fields(project_detail: dict):
    try:
        payload_detail = project_detail['payload']
        print("*****************************************************")
        print("payload_detail Done")
        print(payload_detail)
        print("*****************************************************")
        return payload_detail

    except KeyError as e:
        print(f"Error: Missing expected key in project details: {e}")
        return "Error: Missing expected key in project details."
    
    except TypeError:
        print("Error: The project detail provided is not a dictionary.")
        return "Error: Invalid project detail format."


def verify_values_from_query(query, payload, config):
    """
    Verifies that the values filled in the payload are directly captured from the user query or assigned from the config.
    """
    # Tokenize the user query for words and possible values
    query_tokens = re.findall(r'\b\w+\b', query.lower())

    # Verify each field in the payload
    verified_payload = {}
    for field, value in payload.items():
        # Ensure the value is a string before applying .lower()
        if isinstance(value, str) and value.lower() in query_tokens:
            # If the value is found in the query, accept it
            verified_payload[field] = value
        elif value == config.get(field, "None"):
            # If the value matches the assigned value from the config, accept it
            verified_payload[field] = value
        else:
            # Otherwise, assume the model made an assumption, set it to None and log the issue
            #print(f"Field '{field}' contains assumed value '{value}'. Resetting to None.")
            verified_payload[field] = "None"

    return verified_payload


async def fill_payload_values(websocket: WebSocket, query: str, payload_details: dict, jsonfile: str) -> Dict[str, Any]:
    client = Groq(api_key=groq_api2)
    try:
        response = client.chat.completions.create(
        model='mixtral-8x7b-32768',
        messages=[
            {
                "role": "system",
                "content": f"""You are an expert in filling payload values from a user query based on a configuration file.

                        Strict Instructions:
                        1. **Capture Only from User Query:** Extract values strictly from the user query: {query}. Do **not** infer or assume any values.                        
                        2. **Use Assigned Values:** If a value is missing in the user query or doesn't match the required format/choices, **use the assigned value** specified in the configuration file {payload_details}.        
                        3. **Fill Missing Fields with Assigned Values:** For each field not found in the user query, refer to the configuration file for the field's assigned value. If no valid input is found in the query and no assigned value is provided, use "None".
                        4. **JSON Response Format:** Return only the payload JSON response in the following format, enclosed with `~~~` before and after the response.
                    
                    Example output format:
                        query: get leave records by month and year
                        ~~~{{
                            "payload": {{
                                "employee_id": "None",
                                "monthnumber": "None",
                                "yearnumber": "None"
                            }}
                        }}~~~
                """
            },
            {
                "role": "user",
                "content": f"Analyze the following query: {query} with config file: {payload_details} and extract values based on the user input or use assigned values from the config file."
            }
        ]
    )
    
    except Exception as e:
        logger.error(f"Error during API call: {e}")
        await websocket.send_text(e)
        return "Internal server error"
    try:
        response_text = response.choices[0].message.content.strip()
        json_start_idx = response_text.find("~~~")
        json_end_idx = response_text.rfind("~~~") + 1
        result = response_text[json_start_idx:json_end_idx]
        # Sanitize the response
        sanitized_response = sanitize_json_string(result)
        #logger.info(f"Sanitized response: {sanitized_response}")
        try:
            # Try to parse the JSON response
            result = json.loads(sanitized_response)
            response_config = result.get('payload', {})
            verified_payload = verify_values_from_query(query, response_config, payload_details)

            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Fill payload Done")
            print(verified_payload)
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            return verified_payload
        
        except json.JSONDecodeError:
            logger.error("Error: Failed to decode JSON from the response.")
            await websocket.send_text("Error: The response format is incorrect. Please try again.")
            return {}
        
    except Exception as e:
        logger.error(f"Error while processing the response: {e}")
        await websocket.send_text(e)
        return "Internal server error"
    

def validate(payload_detail, response_config):
    payload_details = payload_detail['payload']
    validated_payload = {}
    
    for key, values in payload_details.items():
        if key in response_config.keys():
            value = response_config.get(key)
            required = values.get('required', False)
            
            # If the field is required and missing, set to None
            if value is None:
                if required:
                    validated_payload[key] = None
                continue
            
            # Check datatype and format
            datatype = values['datatype']
            
            if datatype == 'regex':
                pattern = values['format']
                if not re.match(pattern, value):
                    validated_payload[key] = None
                    continue
            
            elif datatype == 'date':
                formats = values.get('formats', [])
                if not formats:
                    formats = [
            '%Y-%m-%d',       # 2024-09-13
            '%Y/%m/%d',       # 2024/09/13           
            '%Y.%m.%d',       # 2024.09.13
            '%Y %b %d',       # 2024 Sep 13]
                    ]   
                value = value.strip()
                valid_date = False
                for fmt in formats:
                    try:
                        datetime.strptime(value, fmt)
                        valid_date = True
                        break
                    except ValueError:
                        continue
                
                if not valid_date:
                    validated_payload[key] = None
                    continue
            
            elif datatype == 'choices':
                choices = values['choices']
                if value not in choices:
                    validated_payload[key] = None
                    continue
            
            elif datatype == 'string' and value != 'None':
                if not isinstance(value, str):
                    validated_payload[key] = None
                    continue
            
            elif datatype == 'integer':
                try:
                    # Try to cast the value to an integer
                    int(value)
                except ValueError:
                    validated_payload[key] = None
                    continue
            
            elif datatype == 'mobile':
                try:
                    # Check if the value is an integer and has 10 digits
                    int_value = int(value)
                    if len(str(int_value)) != 10:
                        validated_payload[key] = None
                        continue
                except ValueError:
                    validated_payload[key] = None
                    continue
            
            # If all checks pass, keep the value
            validated_payload[key] = value
    
    final_response = {
        'project': payload_detail['project'],
        'url': payload_detail['url'],
        'method': payload_detail['method'],
        'payload': validated_payload
    }
    
    print("*****************************************************************************************************")
    print("Validation Done")
    print(final_response)
    print("*****************************************************************************************************")
    
    return final_response


async def update_process_with_user_input(websocket: WebSocket, project_details: dict, data: dict):
    try:
        update_payload = data['payload']
        # Send available fields to the user
        available_fields = list(update_payload.keys())
        if len(available_fields) <= 2:
            print('less than 2')
            verified_fields = available_fields
        else:
            available_field=[]
            for key,value in project_details['payload'].items():
                if  value['required'] == False:
                    available_field.append(key)   
            await websocket.send_text("Enter 'All' if fields needs to be updated (or)")
            await websocket.send_text("Enter the field names you want to update, 'separated by commas'")
            await websocket.send_text(f"{available_field} ")
            fields_input = await websocket.receive_text()
            fields_input = json.loads(fields_input)
            fields_input = fields_input.get('message')    
            # Handle the case where the user might not input anything or input invalid data
            if not fields_input:
                await websocket.send_text("No fields provided. Please try again.")
                return None
            
            if  fields_input.lower() == 'all':
                print('all')
                print(available_fields)
                verified_fields = available_fields
            else:
                print('selected columns')
                fields_to_update = [field.strip().replace("'", "").replace("[", "").replace("]", "") for field in fields_input.split(',')]
                verified_fields = [field for field in fields_to_update if field and field in available_fields]
                

                for key,value in project_details['payload'].items():
                    if  value['required'] == True:
                        print(key)
                        if key not in verified_fields:
                            verified_fields.append(key)
                        else:
                            print("all true fields present")
                print(verified_fields)
                
    
        if not verified_fields:
            await websocket.send_text("No Verified Fields check update_process_with_user_input.")

        # Initialize updated fields with 'None'
        updated_fields = {}
        for i in verified_fields:
            updated_fields[i] = 'None'
        
        updated = {'project': project_details['project'],
                'url': project_details['url'],
                'method': project_details['method'],
                'payload': updated_fields} 
                
        # print("*****************************************************")
        # print('New updated fields:', updated)
        # print("*****************************************************")
        
        response = await ask_user(websocket, project_details, updated)
        print(response)
        return response

    except Exception as e:
        print(f"Error occurred in update_process_with_user_input: {e}")
        await websocket.send_text("An error occurred while processing your request. Please try again.")
        return None

async def update_process(websocket: WebSocket, project_details:dict,data: dict):
    update_payload = data['payload']
    if all(value is None or value == "None"  for value in update_payload.values()):
        print('start1')
        updated_details = await update_process_with_user_input(websocket,project_details, data)
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("update output:",updated_details)
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        return updated_details
    else:
        print('start2')
        b = data['payload']
        filtered_payload = {}
        
        # Filter out None and "None" values from the payload
        for key, value in b.items():
            if value is not None and value != "None":
                filtered_payload[key] = value
        
        # Create a new dictionary including project, url, method, and filtered payload
        result = {
            'project': data['project'],
            'url': data['url'],
            'method': data['method'],
            'payload': filtered_payload
        }
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("update output direct:",result)
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        return result
    
    
async def ask_user(websocket: WebSocket, pro, pay):
    abc = pay['payload'].copy()
    for key, value in abc.items():
        if value is None or value == "None":
            des = pro['payload'][key]['description']
            #logger.info(f"Sending description to client for {key}: {des}")
            await websocket.send_text(f"Please provide {des}")
            #logger.info("Message sent to WebSocket, waiting for response...")
            user_input = await websocket.receive_text()
            user_input_data = json.loads(user_input)
            abc[key] = user_input_data.get("message")
            valid = validate(pro, abc)
            if valid['payload'][key] is None:
                return await ask_user(websocket, pro, valid)
            else:
                pay['payload'][key] = abc[key]
    return pay

import logging

def nlp_response(answer, payload): 
    try:
        client = Groq(api_key=groq_api3)
        response = client.chat.completions.create(
            model='mixtral-8x7b-32768',
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are an AI assistant responsible for explaining technical SQL operation results in simple and user-friendly terms. 
                    The user has performed a CRUD operation (Create, Read, Update, Delete) using an API that interacts with a database.
                    
                    Provide a concise, clear summary of the operation result in **under 40 words**. Include the relevant payload values.
                    Avoid technical jargon and ensure the explanation is easily understandable by non-technical users.
                    """
                },
                {
                    "role": "user",
                    "content": f"The API response is: {answer}. The payload is: {payload}. Please summarize the result in a user-friendly way."
                }
            ]
        )
    except Exception as e:
        logging.error(f"Error during API call: {e}")
        return "Internal server error"

    try:
        response_text = response.choices[0].message.content.strip()
        return response_text
    except (AttributeError, IndexError, KeyError) as e:
        logging.error(f"Error extracting response from the API: {e}")
        return "Error: Failed to retrieve a valid response from the model."
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "Internal server error."


