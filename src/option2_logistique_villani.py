"""
================================================================================
Option 2 : Simulation logistique méditerranéenne
Système CBU-X — Transport optimal (Villani / Sinkhorn)
Auteur : Marc Daghar
================================================================================
"""
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from scipy.spatial.distance import pdist, squareform
import os

# =============================================================================
# SECTION 1 : Classe Port
# =============================================================================

class Port:
    """Représentation d'un port méditerranéen avec coordonnées géographiques,
    offre et demande en tonnage."""

    def __init__(self, nom, lat, lon, offre, demande):
        self.nom = nom
        self.lat = lat        # Latitude
        self.lon = lon        # Longitude
        self.offre = offre    # Tonnage disponible (normalisé)
        self.demande = demande  # Tonnage requis (normalisé)

    def __repr__(self):
        return f"Port({self.nom}, offre={self.offre:.3f}, demande={self.demande:.3f})"

# =============================================================================
# SECTION 2 : Modèle VillaniLogistics
# =============================================================================

class VillaniLogistics:
    """
    Modèle de transport optimal basé sur l'algorithme de Sinkhorn.
    Implémente la régularisation entropique pour la résolution efficace
    du problème de Monge-Kantorovich discret.

    Références:
        - Villani (2009) : Optimal Transport: Old and New
        - Cuturi (2013) : Sinkhorn Distances
    """

    def __init__(self, ports, epsilon=0.05, max_iter=200, tol=1e-6):
        """
        Args:
            ports: Liste d'objets Port
            epsilon: Paramètre de régularisation entropique
            max_iter: Nombre maximal d'itérations
            tol: Tolérance de convergence
        """
        self.ports = ports
        self.n = len(ports)
        self.epsilon = epsilon
        self.max_iter = max_iter
        self.tol = tol
        self.cost_matrix = None
        self.transport_plan = None
        self.wasserstein_distance = None

    def build_cost_matrix(self):
        """
        Construit la matrice de coût C_ij combinant distance géographique
        et facteur de péage aléatoire.
        """
        positions = np.array([[p.lat, p.lon] for p in self.ports])
        distances = squareform(pdist(positions, 'euclidean'))

        # Facteur de péage aléatoire (symétrique)
        np.random.seed(42)
        peages = np.random.uniform(0, 0.3, (self.n, self.n))
        peages = (peages + peages.T) / 2
        np.fill_diagonal(peages, 0)

        self.cost_matrix = distances + peages
        return self.cost_matrix

    def sinkhorn(self):
        """
        Algorithme de Sinkhorn pour le transport optimal régularisé.
        Résout : P* = argmin_{P in U(a,b)} <P,C> - epsilon * H(P)

        Returns:
            np.ndarray: Matrice de transport optimale P*
        """
        a = np.array([p.offre for p in self.ports])
        b = np.array([p.demande for p in self.ports])

        # Normalisation des marges
        a = a / a.sum()
        b = b / b.sum()

        # Matrice de Gibbs
        K = np.exp(-self.cost_matrix / self.epsilon)

        # Initialisation des multiplicateurs
        u = np.ones(self.n)
        v = np.ones(self.n)

        # Itérations de Sinkhorn
        for iteration in range(self.max_iter):
            u_prev = u.copy()

            # Mise à jour alternative
            v = b / (K.T @ u + 1e-12)
            u = a / (K @ v + 1e-12)

            # Critère de convergence
            if np.linalg.norm(u - u_prev) < self.tol:
                print(f"✅ Sinkhorn converge après {iteration+1} itérations")
                break
        else:
            print(f"⚠️ Sinkhorn n'a pas convergé en {self.max_iter} itérations")

        # Plan de transport optimal
        self.transport_plan = np.diag(u) @ K @ np.diag(v)

        # Distance de Wasserstein-1
        self.wasserstein_distance = np.sum(self.transport_plan * self.cost_matrix)

        return self.transport_plan

    def compute_ricci_curvature(self):
        """
        Calcule la courbure d'Ollivier-Ricci approchée pour chaque paire de ports.
        Ricci(i,j) = 1 - W1(mu_i, mu_j) / d(i,j)

        Returns:
            np.ndarray: Matrice de courbure de Ricci
        """
        if self.transport_plan is None:
            self.sinkhorn()

        curvature_matrix = np.zeros((self.n, self.n))

        for i in range(self.n):
            for j in range(self.n):
                if i != j:
                    d_ij = self.cost_matrix[i, j]
                    W1 = self.wasserstein_distance
                    curvature_matrix[i, j] = 1 - W1 / (d_ij + 1e-12)

        return curvature_matrix

    def detect_bottlenecks(self, threshold=-0.1):
        """
        Détecte les goulots d'étranglement logistiques (courbure négative).

        Args:
            threshold: Seuil de courbure pour définir un goulot

        Returns:
            list: Liste des paires de ports en goulot d'étranglement
        """
        curvature = self.compute_ricci_curvature()
        bottlenecks = []

        for i in range(self.n):
            for j in range(i+1, self.n):
                if curvature[i, j] < threshold:
                    bottlenecks.append((
                        self.ports[i].nom, 
                        self.ports[j].nom, 
                        curvature[i, j]
                    ))

        return bottlenecks

    def visualize_network(self, output_dir='.'):
        """
        Visualise le réseau de transport optimal avec flux proportionnels.

        Args:
            output_dir: Répertoire de sortie
        """
        G = nx.DiGraph()

        # Ajout des nœuds
        for i, port in enumerate(self.ports):
            G.add_node(i, pos=(port.lon, port.lat), label=port.nom)

        # Ajout des arêtes avec flux
        if self.transport_plan is not None:
            for i in range(self.n):
                for j in range(self.n):
                    if self.transport_plan[i, j] > 0.01:
                        G.add_edge(i, j, weight=self.transport_plan[i, j])

        pos = nx.get_node_attributes(G, 'pos')

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

        # Graphique 1 : Réseau avec flux
        nx.draw(G, pos, ax=ax1, with_labels=True,
                labels=nx.get_node_attributes(G, 'label'),
                node_size=800, node_color='lightblue',
                font_size=10, font_weight='bold',
                edgecolors='black', linewidths=1.5)

        edges = G.edges()
        if edges:
            weights = [G[u][v]['weight'] * 150 for u, v in edges]
            nx.draw_networkx_edges(G, pos, ax=ax1, width=weights, 
                                   alpha=0.6, edge_color='darkblue',
                                   arrowsize=20, arrowstyle='->')

        ax1.set_title('Réseau de transport optimal (flux proportionnels)', 
                      fontsize=13, fontweight='bold')
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')

        # Graphique 2 : Matrice de transport
        im = ax2.imshow(self.transport_plan, cmap='viridis', aspect='auto')
        ax2.set_xlabel('Destination', fontsize=12)
        ax2.set_ylabel('Source', fontsize=12)
        ax2.set_title('Plan de transport optimal P*', fontsize=13, fontweight='bold')
        plt.colorbar(im, ax=ax2, label='Proportion de flux')

        labels = [p.nom for p in self.ports]
        ax2.set_xticks(range(self.n))
        ax2.set_yticks(range(self.n))
        ax2.set_xticklabels(labels, rotation=45, ha='right')
        ax2.set_yticklabels(labels)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/transport_optimal.png', dpi=300, bbox_inches='tight')
        plt.show()
        return fig

    def generate_report(self, output_dir='.'):
        """
        Génère un rapport détaillé de la simulation logistique.

        Args:
            output_dir: Répertoire de sortie
        """
        log = f"""# Simulation logistique CBU-X — Transport optimal (Villani/Sinkhorn)

## Configuration
- Nombre de ports : {self.n}
- Régularisation entropique (ε) : {self.epsilon}
- Itérations max : {self.max_iter}
- Tolérance : {self.tol}

## Résultats
- Distance de Wasserstein-1 : {self.wasserstein_distance:.6f}
- Coût total de transport : {np.sum(self.transport_plan * self.cost_matrix):.6f}

## Plan de transport optimal (matrice P*)
```
{np.array2string(self.transport_plan, precision=4, suppress_small=True)}
```

## Ports configurés
"""
        for port in self.ports:
            log += f"\n- **{port.nom}** : Offre={port.offre:.3f}, Demande={port.demande:.3f}"

        # Courbure de Ricci
        curvature = self.compute_ricci_curvature()
        log += f"\n\n## Courbure de Ricci approchée\n```\n{np.array2string(curvature, precision=4)}\n```"

        # Goulots d'étranglement
        bottlenecks = self.detect_bottlenecks()
        log += "\n\n## Goulots d'étranglement détectés\n"
        if bottlenecks:
            for p1, p2, curv in bottlenecks:
                log += f"\n- ⚠️ **{p1} ↔ {p2}** : courbure = {curv:.4f}"
        else:
            log += "\n✅ Aucun goulot d'étranglement majeur détecté."

        log += f"\n\n## Interprétation\n"
        log += f"- Courbure moyenne : {np.mean(curvature):.4f}\n"
        log += f"- Courbure minimale : {np.min(curvature[curvature != 0]):.4f}\n"
        log += f"- Une courbure négative indique un goulot d'étranglement logistique.\n"
        log += f"- La redistribution du waqf doit privilégier les zones de courbure négative.\n"

        with open(f'{output_dir}/log_villani.md', 'w', encoding='utf-8') as f:
            f.write(log)

        return log

# =============================================================================
# SECTION 3 : Point d'entrée principal
# =============================================================================

def main():
    """Exécution complète de l'Option 2"""
    print("=" * 60)
    print("🌊 OPTION 2 : TRANSPORT OPTIMAL (Villani / Sinkhorn)")
    print("=" * 60)

    print("\n🚢 Initialisation des ports méditerranéens...")
    ports = [
        Port("Marseille", 43.3, 5.4, 0.40, 0.25),
        Port("Bizerte", 37.3, 9.9, 0.20, 0.35),
        Port("Istanbul", 41.0, 29.0, 0.25, 0.20),
        Port("Odessa", 46.5, 30.7, 0.15, 0.20)
    ]

    print("📐 Construction du modèle de transport...")
    model = VillaniLogistics(ports, epsilon=0.05, max_iter=200)
    model.build_cost_matrix()

    print("⚙️ Résolution du transport optimal (Sinkhorn)...")
    transport = model.sinkhorn()

    print("🔍 Calcul de la courbure de Ricci...")
    curvature = model.compute_ricci_curvature()

    print("📊 Visualisation du réseau...")
    model.visualize_network()

    print("📝 Génération du rapport...")
    model.generate_report()

    print("\n" + "=" * 60)
    print("✅ OPTION 2 TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)
    print("📁 Fichiers générés :")
    print("   • transport_optimal.png")
    print("   • log_villani.md")

if __name__ == "__main__":
    main()
