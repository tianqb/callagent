"""
Helper functions for the CallAgent project.
"""

import json
import time
import uuid
import os
from datetime import datetime


def generate_id(prefix="id"):
    """
    Generate a unique ID.

    Args:
        prefix (str, optional): Prefix for the ID.

    Returns:
        str: Unique ID.
    """
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def timestamp_to_datetime(timestamp):
    """
    Convert a timestamp to a datetime string.

    Args:
        timestamp (float): Timestamp.

    Returns:
        str: Datetime string.
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def datetime_to_timestamp(dt_str):
    """
    Convert a datetime string to a timestamp.

    Args:
        dt_str (str): Datetime string.

    Returns:
        float: Timestamp.
    """
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return dt.timestamp()


def format_duration(seconds):
    """
    Format a duration in seconds to a human-readable string.

    Args:
        seconds (float): Duration in seconds.

    Returns:
        str: Formatted duration.
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"


def truncate_text(text, max_length=100, suffix="..."):
    """
    Truncate text to a maximum length.

    Args:
        text (str): Text to truncate.
        max_length (int, optional): Maximum length.
        suffix (str, optional): Suffix to add to truncated text.

    Returns:
        str: Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def save_json(data, file_path):
    """
    Save data to a JSON file.

    Args:
        data: Data to save.
        file_path (str): Path to the file.

    Returns:
        bool: True if the data was saved successfully.
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON: {str(e)}")
        return False


def load_json(file_path):
    """
    Load data from a JSON file.

    Args:
        file_path (str): Path to the file.

    Returns:
        dict: Loaded data, or None if the file couldn't be loaded.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {str(e)}")
        return None


def merge_dicts(dict1, dict2):
    """
    Merge two dictionaries.

    Args:
        dict1 (dict): First dictionary.
        dict2 (dict): Second dictionary.

    Returns:
        dict: Merged dictionary.
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def filter_dict(d, keys):
    """
    Filter a dictionary to only include certain keys.

    Args:
        d (dict): Dictionary to filter.
        keys (list): Keys to include.

    Returns:
        dict: Filtered dictionary.
    """
    return {k: v for k, v in d.items() if k in keys}


def exclude_keys(d, keys):
    """
    Filter a dictionary to exclude certain keys.

    Args:
        d (dict): Dictionary to filter.
        keys (list): Keys to exclude.

    Returns:
        dict: Filtered dictionary.
    """
    return {k: v for k, v in d.items() if k not in keys}


def flatten_list(nested_list):
    """
    Flatten a nested list.

    Args:
        nested_list (list): Nested list.

    Returns:
        list: Flattened list.
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def chunk_list(lst, chunk_size):
    """
    Split a list into chunks.

    Args:
        lst (list): List to split.
        chunk_size (int): Size of each chunk.

    Returns:
        list: List of chunks.
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry(func, max_attempts=3, delay=1):
    """
    Retry a function multiple times.

    Args:
        func: Function to retry.
        max_attempts (int, optional): Maximum number of attempts.
        delay (float, optional): Delay between attempts in seconds.

    Returns:
        The result of the function, or None if all attempts failed.
    """
    attempts = 0
    while attempts < max_attempts:
        try:
            return func()
        except Exception as e:
            attempts += 1
            if attempts == max_attempts:
                print(f"Failed after {max_attempts} attempts: {str(e)}")
                return None
            print(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay} seconds...")
            time.sleep(delay)


def format_conversation(conversation):
    """
    Format a conversation for display.

    Args:
        conversation (list): List of conversation entries.

    Returns:
        str: Formatted conversation.
    """
    result = []
    for entry in conversation:
        sender_id = entry[1]
        recipient_id = entry[2]
        message = entry[3]
        timestamp = entry[4]
        
        dt_str = timestamp_to_datetime(timestamp) if isinstance(timestamp, float) else timestamp
        result.append(f"[{dt_str}] {sender_id} -> {recipient_id}: {message}")
    
    return "\n".join(result)


def format_memory(memory):
    """
    Format a memory for display.

    Args:
        memory (list): List of memory entries.

    Returns:
        str: Formatted memory.
    """
    result = []
    for entry in memory:
        memory_id = entry[0]
        agent_id = entry[1]
        memory_type = entry[2]
        content = entry[3]
        metadata = entry[4]
        timestamp = entry[5]
        
        dt_str = timestamp_to_datetime(timestamp) if isinstance(timestamp, float) else timestamp
        result.append(f"[{dt_str}] {agent_id} - {memory_type} (ID: {memory_id}):")
        result.append(f"Content: {truncate_text(content, 100)}")
        if metadata:
            try:
                metadata_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
                result.append(f"Metadata: {json.dumps(metadata_dict, indent=2)}")
            except:
                result.append(f"Metadata: {metadata}")
        result.append("")
    
    return "\n".join(result)


def format_planning(planning):
    """
    Format a planning entry for display.

    Args:
        planning (list): List of planning entries.

    Returns:
        str: Formatted planning.
    """
    result = []
    for entry in planning:
        planning_id = entry[0]
        task_id = entry[1]
        agent_id = entry[2]
        plan_type = entry[3]
        content = entry[4]
        status = entry[5]
        created_at = entry[6]
        updated_at = entry[7]
        
        created_str = timestamp_to_datetime(created_at) if isinstance(created_at, float) else created_at
        updated_str = timestamp_to_datetime(updated_at) if isinstance(updated_at, float) else updated_at
        
        result.append(f"[{created_str}] {agent_id} - {plan_type} (ID: {planning_id}, Task: {task_id}):")
        result.append(f"Status: {status}")
        result.append(f"Content: {truncate_text(content, 100)}")
        if created_at != updated_at:
            result.append(f"Updated: {updated_str}")
        result.append("")
    
    return "\n".join(result)


def extract_task_steps(task_description):
    """
    Extract steps from a task description.

    Args:
        task_description (str): Task description.

    Returns:
        list: List of steps.
    """
    # Simple implementation that looks for numbered steps
    lines = task_description.split('\n')
    steps = []
    
    for line in lines:
        line = line.strip()
        # Look for lines that start with a number followed by a period or parenthesis
        if line and (line[0].isdigit() and len(line) > 1 and line[1] in [')', '.', ':']):
            steps.append(line[2:].strip())
        # Also look for lines that start with "Step X"
        elif line.lower().startswith('step ') and len(line) > 5 and line[5].isdigit():
            steps.append(line[line.find(':') + 1:].strip() if ':' in line else line[6:].strip())
    
    # If no steps were found, try to split by sentences
    if not steps and task_description:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', task_description)
        steps = [s.strip() for s in sentences if s.strip()]
    
    return steps


def parse_agent_response(response):
    """
    Parse an agent response to extract structured information.

    Args:
        response (str): Agent response.

    Returns:
        dict: Parsed response.
    """
    # Try to parse as JSON
    try:
        return json.loads(response)
    except:
        pass
    
    # Try to extract key-value pairs
    result = {}
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip()
    
    # If no structured information was found, return the raw response
    if not result:
        result = {'response': response}
    
    return result
