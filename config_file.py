# config.py - Configuration file for PDB-SDF Docking Viewer

import os
from pathlib import Path

class Config:
    """Configuration settings for the docking viewer app"""
    
    # OpenDock settings
    OPENDOCK_ENV_NAME = "opendock"  # Name of your OpenDock conda environment
    OPENDOCK_PATH = "path\\to\\local\\opendock"  # Path to OpenDock installation

    # AutoDock Vina settings
    VINA_EXECUTABLE = "vina"  # Path to vina executable, or just "vina" if in PATH
    DEFAULT_BINDING_SITE = {
        'center': [0, 0, 0],  # Default binding site center [x, y, z]
        'size': [20, 20, 20]  # Default search box size [x, y, z] in Angstroms
    }
    
    # File processing settings
    MAX_LIGANDS_DISPLAY = 1000  # Maximum number of ligands to load at once
    SCORE_PROPERTIES = [
        'docking_score', 'score', 'vina_score', 'affinity', 
        'binding_energy', 'glide_score', 'chemscore'
    ]
    
    # 3D Visualization settings
    VIEWER_CONFIG = {
        'width': 900,
        'height': 700,
        'protein_style': {
            'cartoon': {'color': 'lightblue', 'opacity': 0.8}
        },
        'ligand_style': {
            'stick': {'colorscheme': 'default', 'radius': 0.2}
        },
        'surface_opacity': 0.3,
        'enable_spin': True
    }
    
    # Molecular property filters
    MOLECULAR_FILTERS = {
        'max_mw': 800,      # Maximum molecular weight
        'max_logp': 5,      # Maximum LogP
        'min_score': -15,   # Minimum binding score to display
        'max_score': 0      # Maximum binding score to display
    }
    
    # App appearance
    APP_CONFIG = {
        'page_title': "PDB-SDF Docking Viewer",
        'page_icon': "🧬",
        'layout': "wide",
        'sidebar_width': 350
    }
    
    @classmethod
    def get_binding_site_from_pdb(cls, pdb_content, site_residues=None):
        """
        Calculate binding site center from PDB content
        
        Args:
            pdb_content (str): PDB file content
            site_residues (list): List of residue numbers defining the binding site
            
        Returns:
            dict: Binding site configuration with center and size
        """
        if site_residues is None:
            # Default binding site residues - modify for your protein
            site_residues = list(range(200, 250))
        
        coords = []
        for line in pdb_content.split('\n'):
            if line.startswith('ATOM'):
                try:
                    resnum = int(line[22:26].strip())
                    if resnum in site_residues:
                        x = float(line[30:38].strip())
                        y = float(line[38:46].strip())
                        z = float(line[46:54].strip())
                        coords.append([x, y, z])
                except:
                    continue
        
        if coords:
            import numpy as np
            coords = np.array(coords)
            center = coords.mean(axis=0).tolist()
            
            # Calculate size based on coordinate range + buffer
            ranges = coords.max(axis=0) - coords.min(axis=0)
            size = (ranges + 10).tolist()  # Add 10Å buffer
            
            return {
                'center': [round(c, 2) for c in center],
                'size': [round(s, 2) for s in size]
            }
        
        return cls.DEFAULT_BINDING_SITE
    
    @classmethod
    def validate_environment(cls):
        """
        Validate that required tools are available
        
        Returns:
            dict: Status of each tool
        """
        status = {}
        
        # Check VINA
        try:
            import subprocess
            result = subprocess.run([cls.VINA_EXECUTABLE, '--help'], 
                                  capture_output=True, text=True, timeout=10)
            status['vina'] = result.returncode == 0
        except:
            status['vina'] = False
        
        # Check OpenDock environment
        try:
            result = subprocess.run(['conda', 'env', 'list'], 
                                  capture_output=True, text=True)
            status['opendock_env'] = cls.OPENDOCK_ENV_NAME in result.stdout
        except:
            status['opendock_env'] = False
        
        # Check RDKit
        try:
            from rdkit import Chem
            status['rdkit'] = True
        except:
            status['rdkit'] = False
        
        # Check py3Dmol
        try:
            import py3Dmol
            status['py3dmol'] = True
        except:
            status['py3dmol'] = False
        
        return status

# Protein-specific configurations
# Add your specific protein configurations here
PROTEIN_CONFIGS = {
    '5n9r': {  # Example: USP7 protein
        'name': 'USP7 Ubiquitin-specific peptidase 7',
        'binding_site': {
            'center': [18.5, 5.2, -7.8],  # Approximate binding site center
            'size': [25, 25, 25]
        },
        'key_residues': [219, 262, 275, 276, 277, 278],  # Important binding residues
        'description': 'Deubiquitinating enzyme, drug target'
    },
    
    # Add more protein-specific configurations as needed
    'your_protein': {
        'name': 'Your Protein Name',
        'binding_site': {
            'center': [0, 0, 0],
            'size': [20, 20, 20]
        },
        'key_residues': [],
        'description': 'Your protein description'
    }
}

# Docking software specific settings
DOCKING_CONFIGS = {
    'opendock': {
        'env_activation': f"conda activate {Config.OPENDOCK_ENV_NAME}",
        'python_script': """
import sys
sys.path.append('{opendock_path}')
from opendock import dock_ligand
result = dock_ligand('{protein_file}', '{ligand_smiles}')
print(result)
""",
        'output_parser': 'json'  # or 'sdf', 'text'
    },
    
    'vina': {
        'base_command': [Config.VINA_EXECUTABLE],
        'required_args': ['--receptor', '--ligand', '--center_x', '--center_y', 
                         '--center_z', '--size_x', '--size_y', '--size_z'],
        'optional_args': {
            '--exhaustiveness': 8,
            '--num_modes': 9,
            '--energy_range': 3
        }
    }
}
