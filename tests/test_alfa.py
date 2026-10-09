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



class AccessibilityAndEndingTests(unittest.TestCase):
    def test_books_follow_platforms_reachable_from_floor(self):
        for level in range(3):
            world = main.World(level)
            for platform in world.platforms[1:]:
                self.assertLessEqual(world.FLOOR - platform.top, 85)
            for x, y in world.books:
                self.assertTrue(any(plat.left <= x <= plat.right and plat.top - y == 35
                                    for plat in world.platforms[1:]))

    def test_boss_end_returns_name_without_extra_enter(self):
        class Keys:
            def __getitem__(self, key):
                return False
        world = main.World(2, 900)
        world.boss_unlocked = True
        boss = next(e for e in world.enemies if e.boss)
        world.damage_enemy(boss, boss.hp)
        self.assertEqual(world.update(.016, Keys()), 'name')
        self.assertGreater(world.score, 900)

    def test_name_screen_is_drawn_without_keypress(self):
        from unittest.mock import Mock
        game = object.__new__(main.Game)
        game.draw = Mock()
        game.state = 'name'
        game.world = main.World(2)
        game.name = 'Jogador'
        game.time = 0
        with patch.object(main.pygame.display, 'flip'):
            main.Game.draw_frame(game)
        self.assertEqual(game.draw.overlay.call_count, 1)
        args = game.draw.overlay.call_args.args
        self.assertIn('REGISTRE SEU NOME', args[0])
        self.assertTrue(any('Jogador' in line for line in args[1]))

    def test_enter_saves_name_once(self):
        from unittest.mock import patch as patched
        game = object.__new__(main.Game)
        game.state = 'name'
        game.name = 'Ana'
        game.name_ready = 0
        game.world = main.World(2, 333)
        game.save = {'music': .7, 'effects': .8, 'rankings': []}
        with patched.object(main.pygame.key, 'stop_text_input'), patched.object(main, 'save_settings'):
            main.Game.event(game, main.pygame.event.Event(main.pygame.KEYDOWN, {'key': main.pygame.K_RETURN}))
            main.Game.event(game, main.pygame.event.Event(main.pygame.KEYDOWN, {'key': main.pygame.K_RETURN}))
        self.assertEqual(game.state, 'menu')  # Enter da tela final retorna ao menu.
        self.assertEqual(len(game.save['rankings']), 1)
        self.assertEqual(game.save['rankings'][0]['name'], 'Ana')

if __name__=='__main__':unittest.main()
