import argparse
import random
import requests


def create_collection(qdrant_host, collection_name):
    payload = {
        "vectors": {
            "size": 4,
            "distance": "Dot"
        }
    }
    resp = requests.put(f"{qdrant_host}/collections/{collection_name}", json=payload)
    if resp.status_code != 200:
        print(f"Collection creation failed: {resp.text}")
        exit(-1)


def generate_points(amount):
    batch_size = 100
    for i in range(0, amount, batch_size):
        points = []
        for j in range(i, i + batch_size):
            points.append({
                "id": j,
                "vector": [round(random.uniform(0, 1), 2) for _ in range(4)],
                "payload": {
                    "city": "Berlin" if j % 2 == 0 else "London",
                    "price": j
                }
            })
        yield {"points": points}


def insert_points(qdrant_host, collection_name, batch_json):
    resp = requests.put(
        f"{qdrant_host}/collections/{collection_name}/points?wait=true", json=batch_json
    )
    EXPECTED_ERROR_MESSAGE = "No space left on device"
    if resp.status_code != 200:
        if resp.status_code == 500 and EXPECTED_ERROR_MESSAGE in resp.text:
            requests.put(f"{qdrant_host}/collections/{collection_name}/points?wait=true", json=batch_json)
        else:
            error_response = resp.json()
            print(f"Points insertions failed with response body:\n{error_response}")
            exit(-2)


def search_point(qdrant_host, collection_name):
    query = {
        "vector": [round(random.uniform(0, 1), 2) for _ in range(4)],
        "top": 10,
        "filter": {
            "must": [
                {
                    "key": "city",
                    "match": {
                        "value": "Berlin"
                    }
                }
            ]
        }
    }
    resp = requests.post(
        f"{qdrant_host}/collections/{collection_name}/points/search", json=query
    )

    if resp.status_code != 200:
        print(f"Search failed with status {resp.status_code}: {resp.text}")
        exit(-3)
    return resp.json()


def initialize_qdrant(qdrant_host, collection_name, points_amount):
    create_collection(qdrant_host, collection_name)
    for points_batch in generate_points(points_amount):
        insert_points(qdrant_host, collection_name, points_batch)
        search_point(qdrant_host, collection_name)


def main():
    parser = argparse.ArgumentParser(description="Create and search points in Qdrant under low-disk testing")
    parser.add_argument("collection_name", type=str, help="Collection name")
    parser.add_argument("points_amount", type=int, help="Number of points to insert")
    parser.add_argument("ports", type=int, nargs="+", help="Ports")
    args = parser.parse_args()

    qdrant_host = f"http://127.0.0.1:{args.ports[0]}"
    initialize_qdrant(qdrant_host, args.collection_name, args.points_amount)
    print("SUCCESS")


if __name__ == "__main__":
    main()
