"""Testes de regras sem abrir janela; instalar pygame antes de executar."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import main

class GameplayTests(unittest.TestCase):
    def test_tres_livros_por_fase(self):
        for level in range(3):
            w=main.World(level)
            self.assertEqual(len(w.books),3)

    def test_boss_requires_three_books_and_pedestal(self):
        w=main.World(2)
        w.player.x=w.pedestal-20
        w.collected=2
        w.interact()
        self.assertFalse(w.boss_unlocked)
        w.collected=3
        self.assertEqual(w.interact(),'unlock')
        self.assertTrue(w.boss_unlocked)
        self.assertTrue(w.damage_enemy(next(e for e in w.enemies if e.boss),20))
        self.assertTrue(w.boss_unlocked)  # permanente, inclusive apos dano

    def test_horizontal_and_diagonal_ink(self):
        w=main.World(0)
        self.assertTrue(w.shoot(False))
        self.assertEqual(w.projectiles[0][3],0)
        w.player.shot_cd=0
        self.assertTrue(w.shoot(True))
        self.assertLess(w.projectiles[1][3],0)

    def test_ranking_persists_maximum_five(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(main,'SAVE_DIR',Path(tmp)):
                score={'music':.6,'effects':.2,'rankings':[{'name':str(i),'score':i*10} for i in range(10)]}
                main.save_settings(score)
                reopened=main.load_save()
                self.assertEqual(len(reopened['rankings']),5)
                self.assertEqual(reopened['rankings'][0]['score'],90)
                self.assertEqual(reopened['music'],.6)
                self.assertEqual(reopened['effects'],.2)

if __name__=='__main__':unittest.main()