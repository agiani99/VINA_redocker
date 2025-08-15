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

2. **Upload files:**
   - **PDB file**: Your protein structure
   - **SDF file**: Your ligand poses with scores

3. **Navigate ligands:**
   - Use Previous/Next buttons or dropdown selector
   - Sort by binding scores
   - View 3D structures

4. **Use integrated tools:**
   - **VINA Rescoring**: Recalculate binding scores for current pose
   - **OpenDock**: Run new docking with SMILES input

## File Format Requirements

### PDB Files
- Standard PDB format protein structures
- Should contain ATOM records for the protein
- HETATM records for cofactors/metals are preserved

### SDF Files
- Standard SDF format with 3D coordinates
- Scores can be embedded as:
  - `docking_score` property
  - `score` property  
  - `vina_score` property
  - `affinity` property
  - `binding_energy` property
- If no score property found, the app will look for score values in comment lines

## Customization

### Binding Site Definition
To customize the binding site for VINA rescoring, modify the `run_vina_rescoring` function:

```python
# Default binding site center and size
center = [x, y, z]  # Coordinates of binding site center
size = [20, 20, 20]  # Size of search box in Angstroms
```

### OpenDock Integration
Update the `run_opendock_docking` function with your specific OpenDock installation:

```python
# Adjust the path to your OpenDock installation
sys.path.append('/path/to/your/opendock/installation')
```

### Score Extraction
To add support for additional score property names, modify the `score_keys` list in `parse_sdf_with_scores`:

```python
score_keys = ['docking_score', 'score', 'vina_score', 'affinity', 'binding_energy', 'your_custom_score']
```

## Troubleshooting

### Common Issues

1. **VINA not found:**
   - Ensure AutoDock Vina is installed and in your PATH
   - Test with: `vina --help`

2. **OpenDock environment not found:**
   - Verify environment name: `conda env list`
   - Ensure OpenDock is properly installed in the environment

3. **SDF parsing errors:**
   - Check SDF file format validity
   - Ensure molecules have 3D coordinates
   - Verify score properties are correctly embedded

4. **3D visualization not loading:**
   - Check browser console for JavaScript errors
   - Try refreshing the page
   - Ensure py3Dmol is properly installed

### Performance Tips

- For large SDF files (>1000 molecules), consider filtering or splitting
- VINA rescoring can be slow; consider batch processing for multiple ligands
- Use browser zoom controls for better 3D viewing experience

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
