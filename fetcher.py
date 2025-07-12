"""
step 1 of the Redis-first chain.  This process extracts data from a URL, 
transforms it for client usage, and publishes it to a Redis pub/sub channel.
"""

import json
import requests
from time import sleep
import arrow
import redis

def fetch_data(url: str) -> str:
    """
    Fetch data from a given URL and return it as a dictionary.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data from {url}, status code: {response.status_code}")

def transform_data(data: dict, period: int) -> dict:
    """
    Transform the fetched data for client usage.
    """
    # print(data)
    tnow = arrow.now()
     
    record = {
        "key": "quotes",
        "update": tnow.isoformat(),
        "valid": tnow.shift(seconds=+period).isoformat(),
        "payload": data[0] if isinstance(data, list) and data else data
    }
    return record

def connect_to_redis(host:str) -> redis.Redis:
    """
    Connect to the Redis server.
    """
    return redis.Redis(host=host, port=6379, db=0, decode_responses=True)

def publish_to_redis(client: redis.Redis, channel: str, message: dict) -> None:
    """
    Publish a message to a Redis pub/sub channel.
    """
    # redis_client = redis.Redis(host='localhost', port=6379, db=0)
    client.publish(channel, json.dumps(message))

def main(url: str, client: redis.Redis, channel: str) -> None:
    """
    Main function to fetch, transform, and publish data.
    """
    while True:
        try:
            data = fetch_data(url)
            transformed_data = transform_data(data,53)
            publish_to_redis(client, channel, transformed_data)
            print(f"Data published to channel {channel}")
        except Exception as e:
            print(f"An error occurred: {e}")
        sleep(60)  # Wait for 60 seconds before fetching data again

if __name__ == "__main__":
    # Example usage
    url = "https://ron-swanson-quotes.herokuapp.com/v2/quotes"
    client = connect_to_redis("redis.local")
    channel = "dev_update"
    main(url, client, channel)