"""
================================================================================
Option 3 : Générateur de waqf numérique
Système CBU-X — Contrat intelligent Solidity (DAO islamique)
Auteur : Marc Daghar
================================================================================
"""
import os
from datetime import datetime

# =============================================================================
# SECTION 1 : Classe WaqfGenerator
# =============================================================================

class WaqfGenerator:
    """
    Générateur de contrat intelligent waqf pour le système CBU-X.
    Implémente un mécanisme de redistribution sans intérêt conforme
    aux principes de l'économie islamique (économie du don / Sadaqa).
    """

    def __init__(self, nom_waqf="WaqfClusterMed", 
                 naqib="0x1234567890123456789012345678901234567890"):
        """
        Args:
            nom_waqf: Nom du contrat waqf
            naqib: Adresse du gestionnaire (naqib)
        """
        self.nom_waqf = nom_waqf
        self.naqib = naqib
        self.biens = [
            {"id": "B001", "nom": "Port de Bizerte", "beneficiaire": "0x111..."},
            {"id": "B002", "nom": "Route Marseille-Bizerte", "beneficiaire": "0x222..."},
            {"id": "B003", "nom": "Hubs Istanbul", "beneficiaire": "0x333..."},
            {"id": "B004", "nom": "Stockage Odessa", "beneficiaire": "0x444..."}
        ]
        self.beneficiaires = [
            {"adresse": "0x111...", "nom": "Fondation Permaculture", "part": 30},
            {"adresse": "0x222...", "nom": "Coopérative Logistique", "part": 25},
            {"adresse": "0x333...", "nom": "Fonds Souverain Tunisien", "part": 25},
            {"adresse": "0x444...", "nom": "INRAT (Institut Recherche)", "part": 20}
        ]

    # =============================================================================
    # SECTION 2 : Génération du contrat Solidity
    # =============================================================================

    def generer_contrat_solidity(self):
        """
        Génère le contrat intelligent complet en Solidity ^0.8.0.

        Returns:
            str: Code Solidity complet
        """
        contrat = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title {self.nom_waqf}
 * @dev Waqf numérique pour la coopération méditerranéenne (CBU-X)
 * @author Marc Daghar — Sadaqa-BRI Framework
 * @date {datetime.now().strftime('%Y-%m-%d')}
 * @notice Ce contrat implémente un mécanisme de redistribution sans intérêt
 *         conforme aux principes de l'économie islamique. Les revenus
 *         générés par les actifs logistiques sont redistribués aux
 *         bénéficiaires selon des parts configurables.
 */
contract {self.nom_waqf} {{

    // ======== STRUCTURES ========

    struct Bien {{
        string id;
        string nom;
        address beneficiaire;
        uint256 montant;
        bool actif;
    }}

    struct Redistribution {{
        uint256 timestamp;
        uint256 montantTotal;
        mapping(address => uint256) parts;
    }}

    // ======== ÉVÉNEMENTS ========

    event BienAjoute(string id, string nom, address beneficiaire);
    event RedistributionEffectuee(uint256 indexed timestamp, uint256 montantTotal);
    event PartModifiee(address indexed beneficiaire, uint256 nouvellePart);
    event FraisRecus(address indexed expediteur, uint256 montant);

    // ======== ÉTATS ========

    address public naqib;
    string public nom;
    uint256 public totalBiens;
    uint256 public totalFrais;

    mapping(string => Bien) public biens;
    string[] public listeBiens;

    mapping(address => uint256) public parts;  // Base 10000 (pour précision décimale)
    address[] public listeBeneficiaires;

    Redistribution[] public historique;

    // ======== MODIFIERS ========

    modifier seulementNaqib() {{
        require(msg.sender == naqib, "CBU-X: Seul le naqib peut effectuer cette action");
        _;
    }}

    modifier bienExiste(string memory _id) {{
        require(biens[_id].actif, "CBU-X: Le bien n'existe pas ou est inactif");
        _;
    }}

    // ======== CONSTRUCTEUR ========

    constructor(string memory _nom, address _naqib) {{
        require(_naqib != address(0), "CBU-X: Adresse naqib invalide");
        nom = _nom;
        naqib = _naqib;

        // Initialisation des bénéficiaires par défaut
"""

        for benef in self.beneficiaires:
            contrat += f"""        parts[{benef['adresse']}] = {benef['part'] * 100}; // {benef['part']}%
        listeBeneficiaires.push({benef['adresse']});
"""

        contrat += """    }

    // ======== FONCTIONS DE GESTION ========

    /**
     * @dev Ajoute un bien au waqf
     * @param _id Identifiant unique du bien
     * @param _nom Nom du bien
     * @param _beneficiaire Adresse du bénéficiaire associé
     */
    function ajouterBien(
        string memory _id,
        string memory _nom,
        address _beneficiaire
    ) public seulementNaqib {
        require(!biens[_id].actif, "CBU-X: Ce bien existe deja");
        require(_beneficiaire != address(0), "CBU-X: Adresse invalide");

        biens[_id] = Bien({
            id: _id,
            nom: _nom,
            beneficiaire: _beneficiaire,
            montant: 0,
            actif: true
        });
        listeBiens.push(_id);
        totalBiens++;

        emit BienAjoute(_id, _nom, _beneficiaire);
    }

    /**
     * @dev Reçoit des frais en monnaie CBU-X (payable)
     * @notice Les frais sont collectés en monnaie native (ETH/MATIC)
     *         et redistribués selon les parts définies.
     */
    function recevoirFrais() public payable {
        require(msg.value > 0, "CBU-X: Montant nul");
        totalFrais += msg.value;
        emit FraisRecus(msg.sender, msg.value);
    }

    /**
     * @dev Redistribue les frais collectés aux bénéficiaires
     * @notice Cette fonction garantit la conservation de la masse monétaire :
     *         sum(Part_k) = R_tot. Pas de création ex nihilo.
     */
    function redistribuerRevenus() public seulementNaqib {
        require(totalFrais > 0, "CBU-X: Aucun frais a redistribuer");
        require(listeBeneficiaires.length > 0, "CBU-X: Aucun beneficiaire");

        uint256 montantTotal = totalFrais;

        // Création de l'entrée d'historique
        uint256 index = historique.length;
        historique.push();
        Redistribution storage redistribution = historique[index];
        redistribution.timestamp = block.timestamp;
        redistribution.montantTotal = montantTotal;

        // Calcul du total des parts
        uint256 totalParts = 0;
        for (uint256 i = 0; i < listeBeneficiaires.length; i++) {
            totalParts += parts[listeBeneficiaires[i]];
        }
        require(totalParts > 0, "CBU-X: Total des parts nul");

        // Redistribution proportionnelle
        for (uint256 i = 0; i < listeBeneficiaires.length; i++) {
            address benef = listeBeneficiaires[i];
            uint256 part = (parts[benef] * montantTotal) / totalParts;
            redistribution.parts[benef] = part;

            // Transfert sécurisé
            (bool success, ) = payable(benef).call{value: part}("");
            require(success, "CBU-X: Transfert echoue");
        }

        totalFrais = 0;
        emit RedistributionEffectuee(block.timestamp, montantTotal);
    }

    /**
     * @dev Modifie la part d'un bénéficiaire (mécanisme anti-cyclique)
     * @param _beneficiaire Adresse du bénéficiaire
     * @param _nouvellePart Nouvelle part en pourcentage (base 100)
     * @notice La part peut être ajustée proportionnellement aux besoins :
     *         alpha_k(t) ~ 1 / Besoin_k(t)
     */
    function modifierPart(address _beneficiaire, uint256 _nouvellePart) 
        public seulementNaqib 
    {
        require(_beneficiaire != address(0), "CBU-X: Adresse invalide");
        require(_nouvellePart > 0, "CBU-X: La part doit etre positive");
        require(_nouvellePart <= 100, "CBU-X: La part ne peut exceder 100%");

        parts[_beneficiaire] = _nouvellePart * 100;
        emit PartModifiee(_beneficiaire, _nouvellePart);
    }

    // ======== FONCTIONS DE CONSULTATION (view) ========

    function obtenirPart(address _beneficiaire) public view returns (uint256) {
        return parts[_beneficiaire] / 100;
    }

    function obtenirHistorique() public view returns (uint256[] memory) {
        uint256[] memory timestamps = new uint256[](historique.length);
        for (uint256 i = 0; i < historique.length; i++) {
            timestamps[i] = historique[i].timestamp;
        }
        return timestamps;
    }

    function obtenirMontantTotal() public view returns (uint256) {
        return totalFrais;
    }

    function nombreBeneficiaires() public view returns (uint256) {
        return listeBeneficiaires.length;
    }

    // ======== FONCTION DE RÉCUPÉRATION D'URGENCE ========

    /**
     * @dev Permet au naqib de récupérer les fonds en cas d'urgence
     * @notice À utiliser uniquement en cas de vulnérabilité détectée.
     *         Le naqib est responsable de la redistribution manuelle.
     */
    function recupererFonds() public seulementNaqib {
        require(totalFrais > 0, "CBU-X: Aucun fonds a recuperer");
        uint256 montant = totalFrais;
        totalFrais = 0;
        (bool success, ) = payable(naqib).call{value: montant}("");
        require(success, "CBU-X: Recuperation echouee");
    }

    // ======== RECEIVE / FALLBACK ========

    receive() external payable {
        recevoirFrais();
    }

    fallback() external payable {
        recevoirFrais();
    }
}
"""
        return contrat

    # =============================================================================
    # SECTION 3 : README de déploiement
    # =============================================================================

    def generer_readme(self, output_dir='.'):
        """
        Génère le README complet pour le déploiement du contrat.

        Args:
            output_dir: Répertoire de sortie
        """
        readme = f"""# {self.nom_waqf} — Contrat intelligent de waqf numérique (CBU-X)

## 📖 Description
Ce contrat intelligent implémente un **waqf numérique** pour la gestion d'actifs logistiques en Méditerranée dans le cadre du système monétaire CBU-X. Il permet de collecter les frais générés par les infrastructures (ports, routes, hubs) et de les redistribuer aux bénéficiaires selon des proportions configurables, sans création monétaire ex nihilo et sans intérêt.

## 🏛️ Architecture

### Acteurs
| Rôle | Description |
|------|-------------|
| **Naqib** | Gestionnaire du waqf (adresse : `{self.naqib}`) |
| **Bénéficiaires** | Organisations recevant les redistributions |

### Biens gérés
"""
        for bien in self.biens:
            readme += f"\n- **{bien['id']}** : {bien['nom']} → {bien['beneficiaire']}"

        readme += "\n\n### Bénéficiaires et parts initiales\n"
        for benef in self.beneficiaires:
            readme += f"\n- **{benef['nom']}** : {benef['part']}% (adresse : {benef['adresse']})"

        readme += f"""

## ⚙️ Fonctionnalités principales

| Fonction | Description | Accès |
|----------|-------------|-------|
| `ajouterBien()` | Ajoute un nouveau bien au waqf | Naqib uniquement |
| `recevoirFrais()` | Reçoit les frais (payable) | Public |
| `redistribuerRevenus()` | Redistribue selon les parts | Naqib uniquement |
| `modifierPart()` | Ajuste les parts (anti-cyclique) | Naqib uniquement |
| `obtenirPart()` | Consulte la part d'un bénéficiaire | Public (view) |
| `recupererFonds()` | Récupération d'urgence | Naqib uniquement |

## 🚀 Déploiement

### Prérequis
- Node.js (v18+) et npm
- Hardhat
- Wallet MetaMask avec ETH de test (Sepolia)

### Installation
```bash
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npx hardhat init
```

### Script de déploiement (`scripts/deploy.js`)
```javascript
const hre = require("hardhat");

async function main() {{
  const Waqf = await hre.ethers.getContractFactory("{self.nom_waqf}");
  const waqf = await Waqf.deploy("{self.nom_waqf}", "{self.naqib}");
  await waqf.waitForDeployment();
  console.log("Waqf déployé à :", await waqf.getAddress());
}}

main().catch((error) => {{
  console.error(error);
  process.exitCode = 1;
}});
```

### Exécution
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

## 🔗 Intégration CBU-X
Le contrat est conçu pour fonctionner avec la monnaie complémentaire CBU-X (panier RUB + UAH + GEL + TRY). Les frais sont collectés en monnaie native et redistribués proportionnellement.

## 📝 Licence
MIT — Open source

---
*Généré par le Sadaqa-BRI Framework — Système CBU-X*
"""

        with open(f'{output_dir}/README_option3.md', 'w', encoding='utf-8') as f:
            f.write(readme)

        return readme

# =============================================================================
# SECTION 4 : Point d'entrée principal
# =============================================================================

def main():
    """Exécution complète de l'Option 3"""
    print("=" * 60)
    print("🏛️ OPTION 3 : WAQF NUMÉRIQUE (Contrat intelligent Solidity)")
    print("=" * 60)

    print("\n🕌 Génération du contrat waqf numérique...")
    generator = WaqfGenerator()

    print("📝 Écriture du contrat Solidity...")
    contrat = generator.generer_contrat_solidity()
    with open('waqf_cluster.sol', 'w', encoding='utf-8') as f:
        f.write(contrat)

    print("📖 Génération du README de déploiement...")
    generator.generer_readme()

    print("\n" + "=" * 60)
    print("✅ OPTION 3 TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)
    print("📁 Fichiers générés :")
    print("   • waqf_cluster.sol")
    print("   • README_option3.md")

if __name__ == "__main__":
    main()
