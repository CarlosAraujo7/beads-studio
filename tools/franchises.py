"""Organização do catálogo POR FRANQUIA (reorganização de 2026-10-25).

Cada categoria da galeria é uma franquia/obra (Naruto, One Piece, Pokémon…). O que não foi identificado fica em "Outros"
(id `other`), com a série antiga como subgrupo, para o usuário ajustar depois.

  CATEGORIES : (id, nome, ícone) na ordem em que aparecem na galeria (o "Outros" é sempre o último)
  GROUP_MAP  : série antiga -> id da categoria (vale para todos os templates da série)
  NAME_MAP   : nome do template -> id da categoria (vence o GROUP_MAP)

Usado por tools/reorganize.py (aplicação única) e por tools/add_templates.py (série nova = categoria nova).
"""
A, G, H, C, T, S = 'cAnime', 'cGames', 'cHeroes', 'cCinema', 'cToons', 'cSymbols'
CATEGORIES = [
    # --- animes e mangás
    ('naruto', 'Naruto', A), ('one-piece', 'One Piece', A), ('dragon-ball', 'Dragon Ball', A), ('cavaleiros-do-zodiaco', 'Cavaleiros do Zodíaco', A),
    ('attack-on-titan', 'Attack on Titan', A), ('jujutsu-kaisen', 'Jujutsu Kaisen', A), ('bleach', 'Bleach', A),
    ('demon-slayer', 'Demon Slayer', A), ('katekyo-hitman-reborn', 'Katekyo Hitman Reborn', A), ('fullmetal-alchemist', 'Fullmetal Alchemist', A),
    ('hunter-x-hunter', 'Hunter x Hunter', A), ('yu-gi-oh', 'Yu-Gi-Oh', A), ('fairy-tail', 'Fairy Tail', A), ('d-gray-man', 'D.Gray-man', A),
    ('trigun', 'Trigun', A), ('my-hero-academia', 'My Hero Academia', A), ('code-geass', 'Code Geass', A), ('konosuba', 'KonoSuba', A),
    ('tokyo-ghoul', 'Tokyo Ghoul', A), ('re-zero', 'Re:Zero', A), ('black-clover', 'Black Clover', A), ('dan-da-dan', 'Dan Da Dan', A),
    ('inuyasha', 'Inuyasha', A), ('assassination-classroom', 'Assassination Classroom', A), ('soul-eater', 'Soul Eater', A),
    ('kaiju-n-8', 'Kaiju nº 8', A), ('frieren', 'Frieren', A), ('tensura', 'Tensura (Slime)', A),
    ('yu-yu-hakusho', 'Yu Yu Hakusho', A), ('death-note', 'Death Note', A), ('inazuma-eleven', 'Inazuma Eleven', A), ('hellsing', 'Hellsing', A),
    # --- jogos
    ('pokemon', 'Pokémon', G), ('mario', 'Mario', G), ('minecraft', 'Minecraft', G), ('plants-vs-zombies', 'Plants vs Zombies', G),
    ('crash-bandicoot', 'Crash Bandicoot', G), ('sonic', 'Sonic', G), ('angry-birds', 'Angry Birds', G), ('stardew-valley', 'Stardew Valley', G),
    ('pou', 'Pou', G), ('skyrim', 'Skyrim', G), ('red-dead-redemption', 'Red Dead Redemption', G), ('assassins-creed', "Assassin's Creed", G),
    ('kirby', 'Kirby', G), ('duolingo', 'Duolingo', G), ('google-chrome', 'Google Chrome', G), ('uno', 'UNO', G), ('god-of-war', 'God of War', G),
    # --- quadrinhos
    ('marvel', 'Marvel', H), ('dc-comics', 'DC Comics', H),
    # --- filmes e séries
    ('harry-potter', 'Harry Potter', C), ('studio-ghibli', 'Studio Ghibli', C), ('star-wars', 'Star Wars', C), ('chaves-e-chapolin', 'Chaves e Chapolin', C),
    ('o-mentalista', 'O Mentalista', C), ('doctor-who', 'Doctor Who', C), ('senhor-dos-aneis', 'O Senhor dos Anéis', C), ('power-rangers', 'Power Rangers', C),
    ('percy-jackson', 'Percy Jackson', C), ('michael-jackson', 'Michael Jackson', C),
    ('how-i-met-your-mother', 'How I Met Your Mother', C), ('la-la-land', 'La La Land', C),
    # --- desenhos
    ('lilo-stitch', 'Lilo & Stitch', T), ('hello-kitty', 'Hello Kitty', T), ('meninas-superpoderosas', 'Meninas Superpoderosas', T),
    ('avatar', 'Avatar: A Lenda de Aang', T), ('winx-club', 'Winx Club', T), ('looney-tunes', 'Looney Tunes', T),
    ('como-treinar-o-seu-dragao', 'Como Treinar o seu Dragão', T), ('zootopia', 'Zootopia', T), ('carros', 'Carros', T), ('minions', 'Minions', T),
    ('bob-esponja', 'Bob Esponja', T), ('hora-de-aventura', 'Hora de Aventura', T), ('phineas-e-ferb', 'Phineas e Ferb', T),
    ('turma-da-monica', 'Turma da Mônica', T), ('ursinho-pooh', 'Ursinho Pooh', T), ('peter-pan', 'Peter Pan', T), ('ratatouille', 'Ratatouille', T),
    ('coragem', 'Coragem, o Cão Covarde', T), ('jovens-titas', 'Jovens Titãs', T), ('ben-10', 'Ben 10', T), ('tartarugas-ninja', 'Tartarugas Ninja', T),
    ('divertida-mente', 'Divertida Mente', T), ('kung-fu-panda', 'Kung Fu Panda', T),
    # --- remessa 24
    ('nanatsu-no-taizai', 'Nanatsu no Taizai', A), ('mortal-kombat', 'Mortal Kombat', G), ('shovel-knight', 'Shovel Knight', G), ('devil-may-cry', 'Devil May Cry', G),
    ('invencivel', 'Invencível', H), ('spawn', 'Spawn', H), ('hellboy', 'Hellboy', H), ('coraline', 'Coraline', T),
    ('piratas-do-caribe', 'Piratas do Caribe', C), ('john-wick', 'John Wick', C), ('game-of-thrones', 'Game of Thrones', C), ('brinquedo-assassino', 'Brinquedo Assassino', C),
    ('o-silencio-dos-inocentes', 'O Silêncio dos Inocentes', C), ('queen', 'Queen', C), ('alien', 'Alien', C),
    # --- remessa 25
    ('final-fantasy', 'Final Fantasy', G), ('fallout', 'Fallout', G), ('overlord', 'Overlord', A), ('round-6', 'Round 6', C), ('o-pequeno-principe', 'O Pequeno Príncipe', T),
    # --- remessa 26
    ('darling-in-the-franxx', 'Darling in the Franxx', A), ('black-butler', 'Black Butler', A), ('hajime-no-ippo', 'Hajime no Ippo', A), ('himouto-umaru-chan', 'Himouto! Umaru-chan', A), ('mega-man', 'Mega Man', G),
    # --- remessa 27
    ('donkey-kong', 'Donkey Kong', G),
    # --- remessa 29
    ('akame-ga-kill', 'Akame ga Kill', A), ('high-school-dxd', 'High School DxD', A), ('kaguya-sama', 'Kaguya-sama', A), ('tokyo-revengers', 'Tokyo Revengers', A),
    ('as-quintuplas', 'As Quíntuplas', A), ('evangelion', 'Evangelion', A), ('mashle', 'Mashle', A), ('the-rising-of-the-shield-hero', 'The Rising of the Shield Hero', A),
    # --- remessa 30
    ('kuroko-no-basket', 'Kuroko no Basket', A), ('eyeshield-21', 'Eyeshield 21', A), ('beelzebub', 'Beelzebub', A), ('wistoria', 'Wistoria', A),
    ('shokugeki-no-soma', 'Shokugeki no Soma', A), ('ao-no-exorcist', 'Ao no Exorcist', A), ('zero-no-tsukaima', 'Zero no Tsukaima', A),
    ('miss-kobayashis-dragon-maid', "Miss Kobayashi's Dragon Maid", A), ('shangri-la-frontier', 'Shangri-La Frontier', A), ('record-of-ragnarok', 'Record of Ragnarok', A),
    ('fate-grand-order', 'Fate/Grand Order', A),
    # --- remessa 31
    ('toy-story', 'Toy Story', T), ('transformers', 'Transformers', T), ('godzilla', 'Godzilla', C), ('dororo', 'Dororo', A), ('zatch-bell', 'Zatch Bell!', A),
    # --- temas específicos
    ('egito-antigo', 'Egito Antigo', S), ('religiao', 'Religião', S), ('gato-da-sorte', 'Gato da sorte', 'cAnimals'),
    ('earrings', 'Brincos', 'cEarrings'),
]
NAME_BY_ID = {i: n for i, n, _ in CATEGORIES}

GROUP_MAP = {
    'Naruto': 'naruto', 'One Piece': 'one-piece', 'Dragon Ball': 'dragon-ball', 'Cavaleiros do Zodíaco': 'cavaleiros-do-zodiaco',
    'Attack on Titan': 'attack-on-titan', 'Jujutsu Kaisen': 'jujutsu-kaisen', 'Bleach': 'bleach', 'Demon Slayer': 'demon-slayer',
    'Hitman Reborn': 'katekyo-hitman-reborn', 'Fullmetal Alchemist': 'fullmetal-alchemist', 'Hunter x Hunter': 'hunter-x-hunter',
    'Yu-Gi-Oh': 'yu-gi-oh', 'Code Geass': 'code-geass', 'KonoSuba': 'konosuba',
    'Pokémon': 'pokemon', 'Mario': 'mario', 'Skyrim': 'skyrim', 'Red Dead Redemption': 'red-dead-redemption', "Assassin's Creed": 'assassins-creed',
    'Harry Potter': 'harry-potter', 'Star Wars': 'star-wars', 'Studio Ghibli': 'studio-ghibli', 'Chaves e Chapolin': 'chaves-e-chapolin',
    'O Mentalista': 'o-mentalista', 'Hello Kitty': 'hello-kitty', 'Minions': 'minions', 'Bob Esponja': 'bob-esponja', 'Avatar': 'avatar',
    'Como Treinar o seu Dragão': 'como-treinar-o-seu-dragao', 'Hora de Aventura': 'hora-de-aventura', 'Phineas e Ferb': 'phineas-e-ferb',
    'Looney Tunes': 'looney-tunes', 'Turma da Mônica': 'turma-da-monica', 'Meninas Superpoderosas': 'meninas-superpoderosas',
    'Winx': 'winx-club', 'Gatos': 'gato-da-sorte', 'Brincos': 'earrings',
}

def _m(cat, *names): return {n: cat for n in names}
NAME_MAP = {}
NAME_MAP.update(_m('hunter-x-hunter', 'Logo de Hunter x Hunter'))
NAME_MAP.update(_m('fairy-tail', 'Emblema de Fairy Tail', 'Natsu Dragneel (chibi)'))
NAME_MAP.update(_m('d-gray-man', 'Allen Walker (D.Gray-man)', 'Lavi (D.Gray-man)'))
NAME_MAP.update(_m('trigun', 'Vash the Stampede (chibi)', 'Vash the Stampede (com arma)'))
NAME_MAP.update(_m('my-hero-academia', 'Deku', 'Shoto Todoroki (chibi)'))
NAME_MAP.update(_m('tokyo-ghoul', 'Kaneki (Tokyo Ghoul)'))
NAME_MAP.update(_m('re-zero', 'Rem (Re:Zero)'))
NAME_MAP.update(_m('black-clover', 'Asta (Black Clover)'))
NAME_MAP.update(_m('dan-da-dan', 'Okarun (Dan Da Dan)'))
NAME_MAP.update(_m('inuyasha', 'Inuyasha (chibi)'))
NAME_MAP.update(_m('assassination-classroom', 'Koro-sensei'))
NAME_MAP.update(_m('soul-eater', 'Lua sorridente (Soul Eater)'))
NAME_MAP.update(_m('kaiju-n-8', 'Gato robô (Kaiju nº 8)'))
NAME_MAP.update(_m('frieren', 'Frieren (chibi)'))
NAME_MAP.update(_m('tensura', 'Rimuru (slime)'))
NAME_MAP.update(_m('minecraft', 'Espada de diamante (Minecraft)', 'Espada de diamante (versão 2)', 'Diamante (Minecraft)', 'Armadura de diamante (Minecraft)'))
NAME_MAP.update(_m('plants-vs-zombies', 'Peashooter (Plants vs Zombies)', 'Girassol (Plants vs Zombies)', 'Cattail (Plants vs Zombies)'))
NAME_MAP.update(_m('crash-bandicoot', 'Aku Aku (Crash Bandicoot)', 'Crash Bandicoot'))
NAME_MAP.update(_m('sonic', 'Shadow (Sonic)', 'Sonic (chibi)'))
NAME_MAP.update(_m('angry-birds', 'Porco verde (Angry Birds)', 'Red (Angry Birds)'))
NAME_MAP.update(_m('stardew-valley', 'Agulha de Irídio (Stardew Valley)', 'Machado de Irídio (Stardew Valley)'))
NAME_MAP.update(_m('pou', 'Pou', 'Pou (padrão)'))
NAME_MAP.update(_m('kirby', 'Kirby'))
NAME_MAP.update(_m('duolingo', 'Coruja do Duolingo'))
NAME_MAP.update(_m('google-chrome', 'Dinossauro do Chrome'))
NAME_MAP.update(_m('uno', 'Carta UNO'))
NAME_MAP.update(_m('marvel', 'Groot (chibi)', 'Groot (no vaso)', 'Wanda Maximoff (Feiticeira Escarlate)', 'Homem-Aranha (chibi)', 'Deadpool',
                   'Homem de Ferro (chibi)', 'Hulk (chibi)', 'Wolverine (Logan chibi)', 'Wolverine (máscara)', 'Visão (Marvel)'))
NAME_MAP.update(_m('dc-comics', 'Símbolo do Lanterna Verde', 'Batman (pixel)', 'Superman (chibi)', 'Logo do Superman'))
NAME_MAP.update(_m('doctor-who', 'TARDIS (Doctor Who)'))
NAME_MAP.update(_m('senhor-dos-aneis', 'Gandalf'))
NAME_MAP.update(_m('power-rangers', 'Power Ranger Vermelho'))
NAME_MAP.update(_m('percy-jackson', 'Percy Jackson (chibi)'))
NAME_MAP.update(_m('michael-jackson', 'Michael Jackson'))
NAME_MAP.update(_m('lilo-stitch', 'Stitch', 'Stitch como Link (Zelda)', 'Stitch (rosto grande)', 'Angel (Lilo & Stitch)', 'Stitch sobre livros'))
NAME_MAP.update(_m('ursinho-pooh', 'Ursinho Pooh'))
NAME_MAP.update(_m('peter-pan', 'Sininho (Tinker Bell)'))
NAME_MAP.update(_m('ratatouille', 'Remy (Ratatouille)'))
NAME_MAP.update(_m('zootopia', 'Judy Hopps (Zootopia)', 'Nick Wilde (Zootopia)'))
NAME_MAP.update(_m('carros', 'Relâmpago McQueen (Carros)', 'Carro azul (Carros)'))
NAME_MAP.update(_m('coragem', 'Coragem, o Cão Covarde'))
NAME_MAP.update(_m('jovens-titas', 'Ravena (Jovens Titãs)'))
NAME_MAP.update(_m('ben-10', 'Omnitrix (Ben 10)'))
NAME_MAP.update(_m('tartarugas-ninja', 'Michelangelo (Tartarugas Ninja)'))
NAME_MAP.update(_m('egito-antigo', 'Olho de Hórus', 'Faraó (mini)', 'Esfinge', 'Ankh (cruz egípcia)'))
NAME_MAP.update(_m('religiao', 'Nossa Senhora Aparecida', 'Nossa Senhora Aparecida (padrão)', 'Sagrado Coração de Jesus', 'Jesus (chibi)'))

GENERIC_GROUPS = {'Outros', 'Outros animes', 'Outros jogos', 'Outros desenhos', 'Outros filmes e séries', 'Animais', 'Símbolos e objetos',
                  'Bichinhos', 'Comidinhas', 'Formas e céu', 'Salvos por você'}


def target(name, group):
    """id da categoria de um template (ou 'other')"""
    return NAME_MAP.get(name) or GROUP_MAP.get(group) or 'other'
