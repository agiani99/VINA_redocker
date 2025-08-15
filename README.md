# PDB-SDF Docking Viewer Setup

## Requirements

Create a `requirements.txt` file:

```txt
streamlit>=1.28.0
pandas>=1.5.0
rdkit-pypi>=2022.9.0
py3Dmol>=2.0.0
numpy>=1.24.0
pathlib
```

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install AutoDock Vina** (for rescoring functionality):
```bash
# Option 1: Using conda
conda install -c conda-forge autodock-vina

# Option 2: Download from official site
# https://vina.scripps.edu/downloads/
```

3. **Set up OpenDock environment:**
```bash
# Create the opendock environment
conda create -n opendock python=3.9
conda activate opendock

# Install OpenDock and its dependencies
# (Follow OpenDock specific installation instructions)
pip install opendock  # or your specific installation method
```

## Usage

1. **Run the app:**
```bash
streamlit run pdb_sdf_docking_viewer.py
```

## Customization

### Score Extraction
To add support for additional score property names, modify the `score_keys` list in `parse_sdf_with_scores`:

```python
score_keys = ['docking_score', 'score', 'vina_score', 'affinity', 'binding_energy', 'your_custom_score']
```

## Advanced Features

### Batch VINA Rescoring
To rescore all ligands at once, you can modify the app to include:

```python
if st.button("🎯 Rescore All Ligands"):
    progress_bar = st.progress(0)
    for i, ligand in enumerate(st.session_state.ligands):
        vina_score = run_vina_rescoring(
            st.session_state.protein_content, 
            ligand['mol_block']
        )
        if vina_score:
            ligand['vina_score'] = vina_score
        progress_bar.progress((i + 1) / len(st.session_state.ligands))
```

### Export Results
Add functionality to export rescored ligands:

```python
if st.button("💾 Export Results"):
    results_df = pd.DataFrame([
        {
            'name': lig['name'],
            'original_score': lig['score'],
            'vina_score': lig.get('vina_score', 'N/A'),
            'mw': lig['mw'],
            'logp': lig['logp']
        }
        for lig in st.session_state.ligands
    ])
    st.download_button(
        "Download CSV",
        results_df.to_csv(index=False),
        "docking_results.csv",
        "text/csv"
    )
```
