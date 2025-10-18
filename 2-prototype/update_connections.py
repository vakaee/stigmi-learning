#!/usr/bin/env python3
"""
Update connections to wire the new Option A flow
"""

import json

def main():
    print("=" * 70)
    print("UPDATING WORKFLOW CONNECTIONS")
    print("=" * 70)

    # Read workflow with new nodes
    with open('workflow-production-ready.json', 'r') as f:
        workflow = json.load(f)

    # Build node name to ID mapping
    node_map = {node['name']: node['id'] for node in workflow['nodes']}

    print("\nNode mapping:")
    for name in ['Load Session', 'Content Feature Extractor', 'Content-Based Router',
                 'Enhanced Numeric Verifier', 'Semantic Validator', 'Classify Stuck',
                 'Build Response Context', 'Route by Category']:
        if name in node_map:
            print(f"  {name}: {node_map[name]}")
        else:
            print(f"  {name}: NOT FOUND")

    # NEW CONNECTIONS FOR OPTION A FLOW
    new_connections = {}

    # 1. Load Session → Content Feature Extractor
    new_connections['Load Session'] = {
        "main": [[{
            "node": "Content Feature Extractor",
            "type": "main",
            "index": 0
        }]]
    }

    # 2. Content Feature Extractor → Content-Based Router
    new_connections['Content Feature Extractor'] = {
        "main": [[{
            "node": "Content-Based Router",
            "type": "main",
            "index": 0
        }]]
    }

    # 3. Content-Based Router → Switch (routes based on _route)
    # We need to create a Switch node or route directly
    # For now, let's route directly to validators

    new_connections['Content-Based Router'] = {
        "main": [[{
            "node": "Enhanced Numeric Verifier",
            "type": "main",
            "index": 0
        }, {
            "node": "Semantic Validator",
            "type": "main",
            "index": 0
        }, {
            "node": "Classify Stuck",
            "type": "main",
            "index": 0
        }]]
    }

    # 4. All validators → Build Response Context
    # (Build Response Context will merge all and route to appropriate handler)

    if 'Build Response Context' in node_map:
        for validator in ['Enhanced Numeric Verifier', 'Semantic Validator', 'Classify Stuck']:
            new_connections[validator] = {
                "main": [[{
                    "node": "Build Response Context",
                    "type": "main",
                    "index": 0
                }]]
            }

    # Preserve existing connections for nodes we didn't change
    existing_keep = [
        'Webhook Trigger',
        'Normalize input',
        'Redis: Get Session',
        'Build Response Context',
        'Route by Category',
        'Response: Unified',
        'Update Session & Format Response',
        'Redis: Save Session',
        'Webhook Response',
        'Synthesis Detector',
        'Synthesis LLM',
        'Parse Synthesis Decision'
    ]

    for node_name, connections in workflow['connections'].items():
        if node_name in existing_keep and node_name not in new_connections:
            new_connections[node_name] = connections

    # Update workflow connections
    workflow['connections'] = new_connections

    # Save
    with open('workflow-production-ready.json', 'w') as f:
        json.dump(workflow, f, indent=2)

    print("\nConnections updated!")
    print(f"Total connection points: {len(new_connections)}")

    return 0

if __name__ == '__main__':
    exit(main())
