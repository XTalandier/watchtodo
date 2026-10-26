#!/usr/bin/env python3
"""
Le défilement de `watchdodo`, dans un VRAI pseudo-terminal.

POURQUOI UN PTY. Sans terminal, le programme ne passe pas en mode brut et
n'arme pas le rapport de souris : la molette n'existe pas, donc le défaut
ne se manifeste pas. Et sans taille IMPOSÉE, la hauteur de vue est celle
du terminal qui lance le test — autant dire inconnue.

CE QU'ON MESURE est ce que la personne voit : le compteur « ↓ N » en bas
d'écran, c'est-à-dire le nombre de lignes encore sous la vue. Aucune
assertion ne porte sur une variable interne. Un test sur `off` serait
resté vert pendant que l'écran ne bougeait pas — c'est précisément ce qui
est arrivé ici, faute de test du tout.

LE DÉFAUT D'ORIGINE : `draw()` ramenait TOUJOURS la vue sur la ligne
sélectionnée. Un cran de molette était donc annulé par le redessin qui le
suivait. Mesuré sur une liste de 173 items : cinq crans déplaçaient la
vue d'une seule ligne, puis elle revenait.
"""

import fcntl
import os
import pty
import re
import select
import shutil
import struct
import sys
import termios
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINAIRE = os.path.join(RACINE, "bin", "watchdodo")

# Les préférences écrites par les cas ne doivent pas atterrir dans le vrai
# fichier de l'utilisateur : un test qui modifie la machine qui le fait
# tourner n'est plus un test.
os.environ["XDG_CONFIG_HOME"] = "/tmp/watchdodo-essai-config"

LIGNES, COLONNES = 30, 100
CRAN = 3  # lignes par cran de molette, comme dans le programme

ANSI = re.compile(r"\x1b\[[0-9;?<>]*[A-Za-z]")

MOLETTE_BAS = b"\x1b[<65;10;10M"
MOLETTE_HAUT = b"\x1b[<64;10;10M"
FLECHE_BAS = b"\x1b[B"
PAGE_HAUT = b"\x1b[5~"


class Ecran:
    """Un `watchdodo` qui tourne, et ce qu'il affiche."""

    def __init__(self, fichier, *options):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.execvp("node", ["node", BINAIRE, *options, fichier])
        fcntl.ioctl(
            self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", LIGNES, COLONNES, 0, 0)
        )
        self.fichier = fichier
        self.tampon = ""
        self.lire(1.0)

    def lire(self, duree=0.14):
        fin = time.time() + duree
        while time.time() < fin:
            pret, _, _ = select.select([self.fd], [], [], 0.05)
            if pret:
                try:
                    self.tampon += os.read(self.fd, 65536).decode("utf8", "replace")
                except OSError:
                    break

    def envoyer(self, octets, fois=1):
        for _ in range(fois):
            os.write(self.fd, octets)
            self.lire()

    def image(self):
        """La dernière image dessinée : chaque `draw()` repart de ESC[H."""
        return ANSI.sub("", self.tampon.split("\x1b[H")[-1])

    def faits_masques(self):
        """
        Vrai quand aucune coche n'est à l'écran.

        PAS sur la mention « [faits masqués] » de l'en-tête : elle est
        TRONQUÉE à la largeur du terminal, et mon premier essai cherchait
        donc une chaîne que l'écran n'affichait jamais en entier. Les
        coches, elles, sont ce que l'œil cherche.
        """
        return "✔" not in self.image()

    def restant(self):
        """Le « ↓ N » du bas d'écran. C'est la position de la vue, vue d'ici."""
        trouve = re.search(r"↓ (\d+)", self.image())
        return int(trouve.group(1)) if trouve else 0

    def fermer(self):
        try:
            os.write(self.fd, b"q")
            self.lire(0.2)
            os.close(self.fd)
        except OSError:
            pass


def liste_longue(chemin):
    """Assez d'items pour que la vue ne puisse pas tout montrer."""
    lignes = ["# Essai de défilement", ""]
    for section in range(4):
        lignes.append(f"## Section {section}")
        lignes.append("")
        for n in range(30):
            # Deux tiers de faits : la proportion d'un projet avancé, et
            # c'est elle qui rend le masquage utile.
            case = "x" if n % 3 else " "
            lignes.append(f"- [{case}] **S{section}-{n}** Un item parmi d'autres `@test`")
        lignes.append("")
    with open(chemin, "w", encoding="utf8") as f:
        f.write("\n".join(lignes))


CAS = []


def cas(nom):
    def enregistrer(fn):
        CAS.append((nom, fn))
        return fn

    return enregistrer


@cas("la molette déplace vraiment la vue")
def _(e):
    # LE DÉFAUT D'ORIGINE EN UNE LIGNE : la vue revenait sur la sélection,
    # donc cinq crans valaient une ligne au lieu de quinze.
    depart = e.restant()
    e.envoyer(MOLETTE_BAS, 5)
    assert e.restant() == depart - 5 * CRAN, (
        f"cinq crans devraient descendre de {5 * CRAN} lignes, "
        f"la vue est passée de {depart} à {e.restant()}"
    )


@cas("et elle remonte pareil")
def _(e):
    e.envoyer(MOLETTE_BAS, 6)
    milieu = e.restant()
    e.envoyer(MOLETTE_HAUT, 2)
    assert e.restant() == milieu + 2 * CRAN


@cas("déplacer la sélection RAMÈNE la vue sur elle")
def _(e):
    # Le pendant du premier cas, et il compte autant : si la vue cessait de
    # suivre la sélection, les flèches sembleraient ne rien faire dès qu'on
    # a fait défiler une fois.
    depart = e.restant()
    e.envoyer(MOLETTE_BAS, 5)
    assert e.restant() != depart
    e.envoyer(FLECHE_BAS)
    assert abs(e.restant() - depart) <= 2, (
        "après une flèche, la vue devrait être revenue près de la sélection, "
        f"elle est à {e.restant()} au lieu de ~{depart}"
    )


@cas("on ne défile pas dans le vide sous la dernière ligne")
def _(e):
    # Le plafond était `rows.length - 1` : on « défilait » sous la fin, et
    # la molette tournait sans que rien ne bouge au retour.
    e.envoyer(MOLETTE_BAS, 80)
    assert e.restant() == 0
    e.envoyer(MOLETTE_BAS, 5)
    assert e.restant() == 0
    e.envoyer(MOLETTE_HAUT, 1)
    assert e.restant() == CRAN, (
        "un cran vers le haut depuis la fin devrait rendre exactement "
        f"{CRAN} lignes, il en rend {e.restant()}"
    )


@cas("une page, c'est la hauteur de la vue")
def _(e):
    # C'était dix items en dur : un saut qui ne correspondait à rien de
    # visible, trop court sur un grand terminal et trop long sur un petit.
    e.envoyer(MOLETTE_BAS, 80)
    e.envoyer(PAGE_HAUT)
    assert e.restant() == LIGNES - 4


@cas("`g` revient en haut, et la vue suit de nouveau")
def _(e):
    # Les chiffres se déduisent du départ : un seuil en dur se serait
    # trompé au premier item ajouté à la liste d'essai. J'ai commencé par
    # en écrire un, et c'est lui qui est tombé — pas le programme.
    depart = e.restant()
    e.envoyer(MOLETTE_BAS, 20)
    assert e.restant() == depart - 20 * CRAN
    e.envoyer(b"g")
    assert e.restant() >= depart - 2, (
        f"après `g`, la vue devrait être revenue tout en haut (~{depart}), "
        f"elle est à {e.restant()}"
    )


@cas("masquer les faits raccourcit vraiment la liste")
def _(e):
    avant = e.restant()
    assert not e.faits_masques()

    e.envoyer(b"a")

    assert e.faits_masques()
    assert e.restant() < avant, (
        f"la liste devrait être plus courte sans les faits : {e.restant()} "
        f"lignes restantes contre {avant}"
    )


@cas("et le choix est RETENU à la prochaine ouverture")
def _(e):
    # C'est tout l'objet du correctif : la touche existait, mais sur une
    # liste de 173 items dont 150 cochés, on la refaisait à chaque fois.
    e.envoyer(b"a")
    assert e.faits_masques()
    e.fermer()

    suivant = Ecran(e.fichier)
    try:
        assert suivant.faits_masques(), (
            "le masquage demandé à la session précédente n'a pas été retenu"
        )
    finally:
        suivant.fermer()


@cas("mais `--all` passe devant la mémoire")
def _(e):
    # Demander explicitement puis voir la préférence d'hier l'emporter
    # serait incompréhensible.
    e.envoyer(b"a")
    assert e.faits_masques()
    e.fermer()

    suivant = Ecran(e.fichier, "--all")
    try:
        assert not suivant.faits_masques()
    finally:
        suivant.fermer()


def main():
    chemin = "/tmp/watchdodo-essai-defilement.md"
    liste_longue(chemin)
    echecs = 0
    for nom, fn in CAS:
        shutil.rmtree(os.environ["XDG_CONFIG_HOME"], ignore_errors=True)
        ecran = Ecran(chemin)
        try:
            fn(ecran)
            print(f"  \033[32m✓\033[0m {nom}")
        except AssertionError as err:
            echecs += 1
            print(f"  \033[31m×\033[0m {nom}\n      {err}")
        finally:
            ecran.fermer()
    print()
    if echecs:
        print(f"\033[31m{echecs} cas en échec sur {len(CAS)}\033[0m")
        sys.exit(1)
    print(f"\033[32m{len(CAS)} cas passent\033[0m")


if __name__ == "__main__":
    main()
