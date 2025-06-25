import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Full data
data = {
    'focal_name': [
        '05-20_C1CC-05', '05-29_K16D-11', '06-08_C1CC-05',
        '06-13_K16D-11', '06-14_C9B-11', '06-29_C1CC-05',
        '06-29_K16D-11', '06-30_C9B-11', '07-20_K16D-11',
        '08-03_C9B-11', '06-02_C9B-11'
    ],
    'test_name': [
        '05-20_C1CC-05', '05-29_K16D-11', '05-20_C1CC-05',
        '05-29_K16D-11', '06-02_C9B-11', '06-08_C1CC-05',
        '06-13_K16D-11', '06-02_C9B-11', '06-13_K16D-11',
        '06-02_C9B-11', '06-02_C9B-11'
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Create a graph from the DataFrame
G = nx.from_pandas_edgelist(df, 'focal_name', 'test_name')

# Find connected components (distinct chains)
components = list(nx.connected_components(G))

# Assign each chain a unique name
chain_map = {}
for i, component in enumerate(components):
    for node in component:
        chain_map[node] = f'Individual_{i+1}'

# Add chain information to the DataFrame
df['chain'] = df['focal_name'].map(chain_map)

# Display the DataFrame
print(df)

# Plotting
plt.figure(figsize=(10, 7))
pos = nx.spring_layout(G)
nx.draw(
    G, pos, with_labels=True, node_size=3000, node_color="skyblue",
    font_size=10, font_color="black", edge_color="gray"
)
plt.show()
