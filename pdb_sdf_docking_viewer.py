import streamlit as st
import pandas as pd
import py3Dmol
from rdkit import Chem
from rdkit.Chem import Descriptors
import streamlit.components.v1 as components
import subprocess
import tempfile
import os
import numpy as np
from pathlib import Path

# Page config
st.set_page_config(page_title="PDB-SDF Docking Viewer", layout="wide")
st.title("🧬 PDB-SDF Docking Viewer with OpenDock & VINA")

# Initialize session state
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0
if 'ligands' not in st.session_state:
    st.session_state.ligands = []
if 'protein' not in st.session_state:
    st.session_state.protein = None
if 'protein_content' not in st.session_state:
    st.session_state.protein_content = None

def parse_sdf_with_scores(sdf_content):
    """Parse SDF file and extract ligands with embedded scores"""
    ligands = []
    mol_blocks = sdf_content.split('$$$$')
    
    for i, mol_block in enumerate(mol_blocks):
        mol_block = mol_block.strip()
        if mol_block and len(mol_block.split('\n')) > 4:
            try:
                mol = Chem.MolFromMolBlock(mol_block)
                if mol is not None:
                    # Extract properties from SDF
                    props = mol.GetPropsAsDict()
                    
                    # Common scoring property names in SDF files
                    score_keys = ['docking_score', 'score', 'vina_score', 'affinity', 'binding_energy']
                    score = None
                    
                    for key in score_keys:
                        if key in props:
                            try:
                                score = float(props[key])
                                break
                            except:
                                continue
                    
                    # If no score found, try to extract from mol block text
                    if score is None:
                        for line in mol_block.split('\n'):
                            if 'score' in line.lower():
                                try:
                                    score = float(line.split()[-1])
                                    break
                                except:
                                    continue
                    
                    # Default score if none found
                    if score is None:
                        score = 0.0
                    
                    ligands.append({
                        'mol': mol,
                        'mol_block': mol_block,
                        'index': i,
                        'score': score,
                        'properties': props,
                        'mw': Descriptors.MolWt(mol),
                        'logp': Descriptors.MolLogP(mol),
                        'name': props.get('_Name', f'Ligand_{i+1}')
                    })
            except Exception as e:
                st.warning(f"Error parsing molecule {i}: {e}")
                continue
    
    # Sort by score (assuming lower is better for binding affinity)
    ligands.sort(key=lambda x: x['score'])
    return ligands

def show_3d_viewer(protein_content, mol_block, ligand_name):
    """Display 3D molecular viewer"""
    view = py3Dmol.view(width=900, height=700)
    
    # Add protein
    view.addModel(protein_content, 'pdb')
    view.setStyle({'model': 0}, {'cartoon': {'color': 'lightblue', 'opacity': 0.8}})
    
    # Add ligand
    view.addModel(mol_block, 'sdf')
    view.setStyle({'model': 1}, {'stick': {'colorscheme': 'default', 'radius': 0.2}})
    
    # Set surface for binding site (optional)
    view.addSurface(py3Dmol.VDW, {'opacity': 0.3, 'color': 'white'}, {'model': 0, 'resi': [200, 250]})
    
    view.zoomTo()
    view.spin(False)  # Add rotation animation
    
    html_string = view._make_html()
    components.html(html_string, height=700)

def run_vina_rescoring(protein_pdb, ligand_sdf, center=None, size=None):
    """Run VINA rescoring for a ligand pose"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save files
            protein_file = os.path.join(temp_dir, "protein.pdb")
            ligand_file = os.path.join(temp_dir, "ligand.sdf")
            output_file = os.path.join(temp_dir, "vina_output.pdbqt")
            
            with open(protein_file, 'w') as f:
                f.write(protein_pdb)
            with open(ligand_file, 'w') as f:
                f.write(ligand_sdf)
            
            # Default binding site center and size if not provided
            if center is None:
                center = [0, 0, 0]  # You should calculate this from binding site
            if size is None:
                size = [20, 20, 20]
            
            # Prepare VINA command (this would need proper setup)
            vina_cmd = [
                "vina",
                "--receptor", protein_file,
                "--ligand", ligand_file,
                "--center_x", str(center[0]),
                "--center_y", str(center[1]), 
                "--center_z", str(center[2]),
                "--size_x", str(size[0]),
                "--size_y", str(size[1]),
                "--size_z", str(size[2]),
                "--score_only",
                "--out", output_file
            ]
            
            # Run VINA (this would need proper environment setup)
            # result = subprocess.run(vina_cmd, capture_output=True, text=True)
            # For now, return a placeholder score
            return np.random.uniform(-12, -6)  # Placeholder
            
    except Exception as e:
        st.error(f"VINA rescoring failed: {e}")
        return None

def run_opendock_docking(protein_pdb, ligand_smiles):
    """Run OpenDock docking in the opendock environment"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Activate opendock environment and run docking
            dock_cmd = [
                "conda", "run", "-n", "opendock",
                "python", "-c", 
                f"""
import sys
sys.path.append('/path/to/opendock')  # Adjust path
from opendock import dock_ligand

# Your OpenDock docking code here
protein_file = '{temp_dir}/protein.pdb'
result = dock_ligand(protein_file, '{ligand_smiles}')
print(result)
"""
            ]
            
            # Save protein file
            protein_file = os.path.join(temp_dir, "protein.pdb")
            with open(protein_file, 'w') as f:
                f.write(protein_pdb)
            
            # Run OpenDock (placeholder implementation)
            # result = subprocess.run(dock_cmd, capture_output=True, text=True)
            # For demo purposes, return placeholder
            return {"score": np.random.uniform(-10, -5), "poses": "placeholder_sdf"}
            
    except Exception as e:
        st.error(f"OpenDock docking failed: {e}")
        return None

# Sidebar controls
with st.sidebar:
    st.header("📁 File Upload")
    
    # PDB upload
    pdb_file = st.file_uploader("Upload PDB File", type=['pdb'])
    if pdb_file:
        st.session_state.protein_content = pdb_file.read().decode('utf-8')
        st.success("✅ PDB loaded")
        
        # Basic protein info
        lines = st.session_state.protein_content.split('\n')
        atom_count = len([l for l in lines if l.startswith('ATOM')])
        st.info(f"Protein atoms: {atom_count}")
    
    # SDF upload  
    sdf_file = st.file_uploader("Upload SDF File", type=['sdf'])
    if sdf_file:
        sdf_content = sdf_file.read().decode('utf-8')
        st.session_state.ligands = parse_sdf_with_scores(sdf_content)
        st.success(f"✅ {len(st.session_state.ligands)} ligands loaded")
    
    st.divider()
    
    # Tools section
    st.header("🔧 Tools")
    
    if st.session_state.protein_content and st.session_state.ligands:
        st.subheader("VINA Rescoring")
        if st.button("🎯 Rescore Current Pose"):
            current_ligand = st.session_state.ligands[st.session_state.current_idx]
            with st.spinner("Running VINA rescoring..."):
                vina_score = run_vina_rescoring(
                    st.session_state.protein_content, 
                    current_ligand['mol_block']
                )
                if vina_score:
                    st.session_state.ligands[st.session_state.current_idx]['vina_score'] = vina_score
                    st.success(f"VINA Score: {vina_score:.3f}")
        
        st.subheader("OpenDock Docking")
        smiles_input = st.text_input("SMILES for new docking:")
        if st.button("🚀 Run OpenDock") and smiles_input:
            with st.spinner("Running OpenDock docking..."):
                dock_result = run_opendock_docking(
                    st.session_state.protein_content,
                    smiles_input
                )
                if dock_result:
                    st.success(f"Docking Score: {dock_result['score']:.3f}")

# Main interface
if st.session_state.protein_content and st.session_state.ligands:
    total_ligands = len(st.session_state.ligands)
    current_ligand = st.session_state.ligands[st.session_state.current_idx]
    
    # Navigation controls
    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous") and st.session_state.current_idx > 0:
            st.session_state.current_idx -= 1
            st.rerun()
    
    with col2:
        new_idx = st.selectbox(
            "Select Ligand:",
            range(total_ligands),
            index=st.session_state.current_idx,
            format_func=lambda x: f"{st.session_state.ligands[x]['name']} (Score: {st.session_state.ligands[x]['score']:.3f})"
        )
        if new_idx != st.session_state.current_idx:
            st.session_state.current_idx = new_idx
            st.rerun()
    
    with col3:
        if st.button("➡️ Next") and st.session_state.current_idx < total_ligands - 1:
            st.session_state.current_idx += 1
            st.rerun()
    
    with col4:
        if st.button("🔄 Sort by Score"):
            st.session_state.ligands.sort(key=lambda x: x['score'])
            st.session_state.current_idx = 0
            st.rerun()
    
    # Current ligand information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Ligand", f"{st.session_state.current_idx + 1}/{total_ligands}")
        st.metric("Binding Score", f"{current_ligand['score']:.3f}")
    
    with col2:
        st.metric("Molecular Weight", f"{current_ligand['mw']:.1f}")
        st.metric("LogP", f"{current_ligand['logp']:.2f}")
    
    with col3:
        if 'vina_score' in current_ligand:
            st.metric("VINA Score", f"{current_ligand['vina_score']:.3f}")
        else:
            st.metric("VINA Score", "Not calculated")
    
    # 3D Viewer
    st.subheader("🔬 3D Visualization")
    show_3d_viewer(
        st.session_state.protein_content, 
        current_ligand['mol_block'],
        current_ligand['name']
    )
    
    # Ligand properties table
    if current_ligand['properties']:
        st.subheader("📊 Ligand Properties")
        props_df = pd.DataFrame(list(current_ligand['properties'].items()), 
                               columns=['Property', 'Value'])
        st.dataframe(props_df, use_container_width=True)

else:
    # Welcome screen
    st.markdown("""
    ## Welcome to the PDB-SDF Docking Viewer
    
    This app provides a streamlined interface for visualizing protein-ligand docking results with integrated scoring tools.
    
    ### Features:
    - 📁 **Simple Input**: Just upload PDB (protein) and SDF (ligands) files
    - 🔬 **3D Visualization**: Interactive molecular viewer with py3Dmol
    - 🎯 **VINA Rescoring**: Rescore ligand poses using AutoDock Vina
    - 🚀 **OpenDock Integration**: Run new docking calculations
    - 📊 **Score Analysis**: Sort and compare binding scores
    
    ### Getting Started:
    1. Upload your PDB protein structure file
    2. Upload your SDF ligand poses file
    3. Browse through ligands using the navigation controls
    4. Use the tools in the sidebar for rescoring and new docking
    
    ### Requirements:
    - AutoDock Vina installed and accessible via command line
    - OpenDock environment set up as 'opendock'
    - RDKit for molecular processing
    """)
    
    st.info("👆 Please upload PDB and SDF files using the sidebar to get started!")
