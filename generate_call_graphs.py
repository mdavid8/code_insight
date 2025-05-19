"""
Generate call graphs for Python files in the repository using pycg and visualize with pyvis.
Creates both function-level and class-level call graphs in interactive HTML format.
"""

import os
import sys
import json
import subprocess
import networkx as nx
from pyvis.network import Network
import re

# Repository directory
REPO_DIR = "/home/ubuntu/projects/head-pose-estimation-and-face-landmark"
# Output directory
OUTPUT_DIR = "/home/ubuntu/call_graphs"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# List of Python files in the repository
python_files = [
    "/home/ubuntu/projects/head-pose-estimation-and-face-landmark/evaluate_48.py",
    "/home/ubuntu/projects/head-pose-estimation-and-face-landmark/facePose.py",
    "/home/ubuntu/projects/head-pose-estimation-and-face-landmark/landmarkPredict.py",
    "/home/ubuntu/projects/head-pose-estimation-and-face-landmark/landmarkPredict_video.py",
    "/home/ubuntu/projects/head-pose-estimation-and-face-landmark/librect.py"
]

def generate_call_graph_data(files):
    """
    Generate call graph data using pycg.
    
    Args:
        files: List of Python files to analyze
    
    Returns:
        Call graph data in JSON format
    """
    # Define the output JSON file
    output_json = os.path.join(OUTPUT_DIR, "call_graph.json")
    
    # Define the command to run pycg
    cmd = [
        "pycg",
        "--package", REPO_DIR,
        "-o", output_json
    ] + files
    
    # Run pycg and capture the output
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Read the generated JSON file
        with open(output_json, 'r') as f:
            call_graph_data = json.load(f)
        
        return call_graph_data
    except subprocess.CalledProcessError as e:
        print(f"Error generating call graph: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error processing call graph data: {e}")
        return None

def extract_function_calls(call_graph_data):
    """
    Extract function-level call graph from the pycg output.
    
    Args:
        call_graph_data: Call graph data from pycg
    
    Returns:
        NetworkX graph of function calls
    """
    G = nx.DiGraph()
    
    # Process each function and its calls
    for func, calls in call_graph_data.items():
        # Skip external libraries
        if not func.startswith(REPO_DIR.replace('/home/ubuntu/', '')):
            continue
            
        # Clean up function name for display
        display_name = func.split('.')[-1]
        module_name = '.'.join(func.split('.')[:-1])
        
        # Add the function node
        G.add_node(func, label=display_name, title=func, group=module_name)
        
        # Add edges for each call
        for call in calls:
            # Skip external libraries
            if not call.startswith(REPO_DIR.replace('/home/ubuntu/', '')):
                continue
                
            # Clean up call name for display
            call_display = call.split('.')[-1]
            call_module = '.'.join(call.split('.')[:-1])
            
            # Add the call node
            G.add_node(call, label=call_display, title=call, group=call_module)
            
            # Add the edge
            G.add_edge(func, call)
    
    return G

def extract_class_calls(call_graph_data):
    """
    Extract class-level call graph from the pycg output.
    
    Args:
        call_graph_data: Call graph data from pycg
    
    Returns:
        NetworkX graph of class calls
    """
    G = nx.DiGraph()
    
    # Map to store function to class mapping
    func_to_class = {}
    
    # First pass: identify classes and their methods
    for func in call_graph_data.keys():
        # Skip external libraries
        if not func.startswith(REPO_DIR.replace('/home/ubuntu/', '')):
            continue
            
        # Check if this is a class method (contains a class name)
        parts = func.split('.')
        if len(parts) >= 3:  # module.class.method
            class_name = '.'.join(parts[:-1])  # module.class
            func_to_class[func] = class_name
            
            # Add the class node if it doesn't exist
            if not G.has_node(class_name):
                display_name = parts[-2]  # class name
                module_name = '.'.join(parts[:-2])  # module
                G.add_node(class_name, label=display_name, title=class_name, group=module_name)
    
    # Second pass: add edges between classes
    for func, calls in call_graph_data.items():
        # Skip if not a class method or external
        if func not in func_to_class:
            continue
            
        source_class = func_to_class[func]
        
        for call in calls:
            # Skip external calls
            if call not in func_to_class:
                continue
                
            target_class = func_to_class[call]
            
            # Skip self-calls within the same class
            if source_class == target_class:
                continue
                
            # Add edge between classes
            G.add_edge(source_class, target_class)
    
    return G

def create_interactive_graph(G, output_file, title):
    """
    Create an interactive HTML visualization of the graph.
    
    Args:
        G: NetworkX graph
        output_file: Output HTML file path
        title: Graph title
    """
    # Create a PyVis network
    net = Network(notebook=False, height="800px", width="100%", directed=True)
    
    # Add nodes and edges from NetworkX graph
    for node, attrs in G.nodes(data=True):
        net.add_node(node, label=attrs.get('label', node), title=attrs.get('title', node), group=attrs.get('group', ''))
    
    for source, target in G.edges():
        net.add_edge(source, target)
    
    # Set options for better visualization
    net.set_options("""
    {
        "nodes": {
            "shape": "dot",
            "size": 20,
            "font": {
                "size": 14,
                "face": "Tahoma"
            }
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": {
                "type": "continuous"
            }
        },
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -80000,
                "centralGravity": 0.3,
                "springLength": 95,
                "springConstant": 0.04
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "barnesHut",
            "stabilization": {
                "enabled": true,
                "iterations": 1000,
                "updateInterval": 100
            }
        }
    }
    """)
    
    # Add title to the HTML
    html_title = f"""
    <h1>{title}</h1>
    <p>Interactive call graph visualization. Drag nodes to rearrange. Zoom with mouse wheel. Click nodes to highlight connections.</p>
    """
    
    # Save the graph to an HTML file
    net.save_graph(output_file)
    
    # Add the title to the HTML file
    with open(output_file, 'r') as f:
        html_content = f.read()
    
    html_content = html_content.replace('<body>', f'<body>\n{html_title}')
    
    with open(output_file, 'w') as f:
        f.write(html_content)

def generate_index_html(function_graphs, class_graphs):
    """
    Generate an index HTML file that links to all generated call graphs.
    
    Args:
        function_graphs: List of function-level graph file paths
        class_graphs: List of class-level graph file paths
    """
    index_file = os.path.join(OUTPUT_DIR, "index.html")
    
    # Create the HTML content
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Python Call Graphs</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #2980b9;
                margin-top: 30px;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                margin-bottom: 10px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            a {
                color: #3498db;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
                color: #2c3e50;
            }
            .description {
                margin-top: 20px;
                padding: 15px;
                background-color: #e8f4fc;
                border-radius: 5px;
                border-left: 5px solid #3498db;
            }
        </style>
    </head>
    <body>
        <h1>Python Call Graphs</h1>
        
        <div class="description">
            <p>This page contains interactive call graphs for the Python files in the 
            <a href="https://github.com/guozhongluo/head-pose-estimation-and-face-landmark" target="_blank">
            head-pose-estimation-and-face-landmark</a> repository.</p>
            <p>The graphs are divided into two categories:</p>
            <ul style="list-style-type: disc; padding-left: 20px;">
                <li><strong>Function-level graphs:</strong> Show the relationships between functions</li>
                <li><strong>Class-level graphs:</strong> Show the relationships between classes</li>
            </ul>
            <p>Click on any link below to view the interactive graph. In the graph view, you can:</p>
            <ul style="list-style-type: disc; padding-left: 20px;">
                <li>Drag nodes to rearrange the graph</li>
                <li>Zoom in/out using the mouse wheel</li>
                <li>Click on nodes to highlight their connections</li>
                <li>Hover over nodes to see additional information</li>
            </ul>
        </div>
    """
    
    # Add function-level graphs
    if function_graphs:
        html_content += """
        <h2>Function-Level Call Graphs</h2>
        <ul>
        """
        
        for graph_file in function_graphs:
            file_name = os.path.basename(graph_file)
            html_content += f'            <li><a href="{file_name}" target="_blank">{file_name}</a></li>\n'
        
        html_content += """
        </ul>
        """
    
    # Add class-level graphs
    if class_graphs:
        html_content += """
        <h2>Class-Level Call Graphs</h2>
        <ul>
        """
        
        for graph_file in class_graphs:
            file_name = os.path.basename(graph_file)
            html_content += f'            <li><a href="{file_name}" target="_blank">{file_name}</a></li>\n'
        
        html_content += """
        </ul>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    # Write the HTML content to the file
    with open(index_file, "w") as f:
        f.write(html_content)
    
    return index_file

def analyze_python_file_structure():
    """
    Analyze the structure of Python files to extract classes and functions.
    This is a fallback method if pycg doesn't work well.
    """
    import ast
    
    class_graphs = []
    function_graphs = []
    
    # Create a combined graph for all files
    combined_function_graph = nx.DiGraph()
    combined_class_graph = nx.DiGraph()
    
    for python_file in python_files:
        file_name = os.path.basename(python_file)
        print(f"Analyzing {file_name}...")
        
        try:
            with open(python_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Parse the Python code
            tree = ast.parse(code)
            
            # Extract classes and functions
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            # Create function-level graph
            function_graph = nx.DiGraph()
            for func in functions:
                function_graph.add_node(func, label=func, title=f"{file_name}:{func}", group=file_name)
                combined_function_graph.add_node(func, label=func, title=f"{file_name}:{func}", group=file_name)
            
            # Create class-level graph
            class_graph = nx.DiGraph()
            for cls in classes:
                class_graph.add_node(cls, label=cls, title=f"{file_name}:{cls}", group=file_name)
                combined_class_graph.add_node(cls, label=cls, title=f"{file_name}:{cls}", group=file_name)
            
            # Try to infer relationships from code (this is a simplified approach)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id') and node.func.id in functions:
                        # This is a direct function call
                        if hasattr(node, 'parent_func') and node.parent_func in functions:
                            function_graph.add_edge(node.parent_func, node.func.id)
                            combined_function_graph.add_edge(node.parent_func, node.func.id)
            
            # Save individual graphs
            if functions:
                output_file = os.path.join(OUTPUT_DIR, f"{file_name.replace('.py', '')}_function.html")
                create_interactive_graph(function_graph, output_file, f"Function Call Graph: {file_name}")
                function_graphs.append(output_file)
                print(f"  Function call graph saved to {output_file}")
            
            if classes:
                output_file = os.path.join(OUTPUT_DIR, f"{file_name.replace('.py', '')}_class.html")
                create_interactive_graph(class_graph, output_file, f"Class Call Graph: {file_name}")
                class_graphs.append(output_file)
                print(f"  Class call graph saved to {output_file}")
                
        except Exception as e:
            print(f"Error analyzing {file_name}: {e}")
    
    # Save combined graphs
    if combined_function_graph.nodes():
        output_file = os.path.join(OUTPUT_DIR, "combined_function.html")
        create_interactive_graph(combined_function_graph, output_file, "Combined Function Call Graph (All Files)")
        function_graphs.append(output_file)
        print(f"Combined function call graph saved to {output_file}")
    
    if combined_class_graph.nodes():
        output_file = os.path.join(OUTPUT_DIR, "combined_class.html")
        create_interactive_graph(combined_class_graph, output_file, "Combined Class Call Graph (All Files)")
        class_graphs.append(output_file)
        print(f"Combined class call graph saved to {output_file}")
    
    return function_graphs, class_graphs

def create_manual_call_graphs():
    """
    Create call graphs manually by parsing Python files.
    This is a fallback method if other methods don't work.
    """
    function_graphs = []
    class_graphs = []
    
    # Create a combined graph for all files
    combined_function_graph = nx.DiGraph()
    combined_class_graph = nx.DiGraph()
    
    # Process each Python file
    for python_file in python_files:
        file_name = os.path.basename
(Content truncated due to size limit. Use line ranges to read in chunks)