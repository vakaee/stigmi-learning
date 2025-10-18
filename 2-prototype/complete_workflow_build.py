#!/usr/bin/env python3
"""
Complete Option A workflow builder
Creates all nodes and connections for the unified classification flow
"""

import json
import uuid

def create_route_switch(base_x, base_y):
    """Create a switch node to route based on _route field"""
    return {
        "parameters": {
            "rules": {
                "values": [
                    {
                        "conditions": {
                            "options": {
                                "caseSensitive": True,
                                "leftValue": "",
                                "typeValidation": "strict",
                                "version": 1
                            },
                            "conditions": [{
                                "leftValue": "={{$json._route}}",
                                "rightValue": "verify_numeric",
                                "operator": {"type": "string", "operation": "equals"},
                                "id": str(uuid.uuid4())
                            }],
                            "combinator": "and"
                        },
                        "renameOutput": True,
                        "outputKey": "verify_numeric"
                    },
                    {
                        "conditions": {
                            "options": {
                                "caseSensitive": True,
                                "leftValue": "",
                                "typeValidation": "strict",
                                "version": 1
                            },
                            "conditions": [{
                                "leftValue": "={{$json._route}}",
                                "rightValue": "validate_conceptual",
                                "operator": {"type": "string", "operation": "equals"},
                                "id": str(uuid.uuid4())
                            }],
                            "combinator": "and"
                        },
                        "renameOutput": True,
                        "outputKey": "validate_conceptual"
                    },
                    {
                        "conditions": {
                            "options": {
                                "caseSensitive": True,
                                "leftValue": "",
                                "typeValidation": "strict",
                                "version": 1
                            },
                            "conditions": [{
                                "leftValue": "={{$json._route}}",
                                "rightValue": "classify_stuck",
                                "operator": {"type": "string", "operation": "equals"},
                                "id": str(uuid.uuid4())
                            }],
                            "combinator": "and"
                        },
                        "renameOutput": True,
                        "outputKey": "classify_stuck"
                    },
                    {
                        "conditions": {
                            "options": {
                                "caseSensitive": True,
                                "leftValue": "",
                                "typeValidation": "strict",
                                "version": 1
                            },
                            "conditions": [{
                                "leftValue": "={{$json._route}}",
                                "rightValue": "teach_back_response",
                                "operator": {"type": "string", "operation": "equals"},
                                "id": str(uuid.uuid4())
                            }],
                            "combinator": "and"
                        },
                        "renameOutput": True,
                        "outputKey": "teach_back_response"
                    }
                ]
            },
            "options": {
                "fallbackOutput": "extra"
            }
        },
        "id": str(uuid.uuid4()),
        "name": "Route by Content Type",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3,
        "position": [base_x + 400, base_y + 200],
        "notes": "Routes to appropriate validator based on message content type"
    }

def main():
    print("=" * 70)
    print("COMPLETE OPTION A WORKFLOW BUILD")
    print("=" * 70)

    # Read workflow
    with open('workflow-production-ready.json', 'r') as f:
        workflow = json.load(f)

    # Build node mapping
    node_map = {node['name']: node for node in workflow['nodes']}

    # Add routing switch node
    load_session = node_map.get('Load Session')
    if not load_session:
        print("ERROR: Load Session not found")
        return 1

    base_x, base_y = load_session['position']

    print("\nAdding Route by Content Type switch...")
    route_switch = create_route_switch(base_x, base_y)
    workflow['nodes'].append(route_switch)
    node_map[route_switch['name']] = route_switch
    print(f"  Created: {route_switch['name']} ({route_switch['id']})")

    # Build new connections
    print("\nBuilding connections...")
    connections = {}

    # Find all our key nodes
    key_nodes = {
        'Load Session': node_map.get('Load Session'),
        'Content Feature Extractor': node_map.get('Content Feature Extractor'),
        'Content-Based Router': node_map.get('Content-Based Router'),
        'Route by Content Type': route_switch,
        'Enhanced Numeric Verifier': node_map.get('Enhanced Numeric Verifier'),
        'Semantic Validator': node_map.get('Semantic Validator'),
        'Classify Stuck': node_map.get('Classify Stuck'),
        'Build Response Context': node_map.get('Build Response Context'),
        'Route by Category': node_map.get('Route by Category')
    }

    for name, node in key_nodes.items():
        if not node:
            print(f"  WARNING: {name} not found")

    # 1. Load Session → Content Feature Extractor
    connections['Load Session'] = {
        "main": [[{"node": "Content Feature Extractor", "type": "main", "index": 0}]]
    }

    # 2. Content Feature Extractor → Content-Based Router
    connections['Content Feature Extractor'] = {
        "main": [[{"node": "Content-Based Router", "type": "main", "index": 0}]]
    }

    # 3. Content-Based Router → Route by Content Type (switch)
    connections['Content-Based Router'] = {
        "main": [[{"node": "Route by Content Type", "type": "main", "index": 0}]]
    }

    # 4. Route by Content Type → validators (via switch outputs)
    connections['Route by Content Type'] = {
        "main": [
            [{"node": "Enhanced Numeric Verifier", "type": "main", "index": 0}],  # verify_numeric
            [{"node": "Semantic Validator", "type": "main", "index": 0}],  # validate_conceptual
            [{"node": "Classify Stuck", "type": "main", "index": 0}],  # classify_stuck
            [{"node": "Classify Stuck", "type": "main", "index": 0}],  # teach_back_response (same as stuck for now)
            []  # fallback
        ]
    }

    # 5. All validators → Build Response Context
    for validator in ['Enhanced Numeric Verifier', 'Semantic Validator', 'Classify Stuck']:
        connections[validator] = {
            "main": [[{"node": "Build Response Context", "type": "main", "index": 0}]]
        }

    # Preserve existing connections for unchanged nodes
    preserve_nodes = [
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
        'Parse Synthesis Decision',
        'Debug: Before Response1',
        'Debug: Execution Data1'
    ]

    for node_name in preserve_nodes:
        if node_name in workflow['connections'] and node_name not in connections:
            connections[node_name] = workflow['connections'][node_name]

    # Update workflow
    workflow['connections'] = connections

    # Count stats
    total_connections = sum(len(v.get('main', [])) for v in connections.values())

    print(f"\nFinal workflow:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Connection points: {len(connections)}")
    print(f"  Total connections: {total_connections}")

    # Save
    with open('workflow-production-ready.json', 'w') as f:
        json.dump(workflow, f, indent=2)

    print("\nWorkflow saved successfully!")
    print("\nOption A workflow is complete!")
    print("\nKey changes:")
    print("  ✓ Single classification path (no dual system)")
    print("  ✓ Content-first routing (not state-based)")
    print("  ✓ Configurable error detection")
    print("  ✓ Configurable semantic validation")
    print("  ✓ Operation error heuristic (45 → stuck, 8 → wrong_operation)")
    print("\nNext: Test with the '45' conversation")

    return 0

if __name__ == '__main__':
    exit(main())
