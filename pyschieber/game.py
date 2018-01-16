from random import shuffle
import logging

from pyschieber.deck import Deck
from pyschieber.rules.stich_rules import stich_rules, card_allowed
from pyschieber.rules.count_rules import count_stich, counting_factor
from pyschieber.stich import PlayedCard

logger = logging.getLogger(__name__)


class Game:
    def __init__(self, teams=None, point_limit=2500):
        self.teams = teams
        self.point_limit = point_limit
        self.players = teams[0].players + teams[1].players
        self.trumpf = None
        self.deck = Deck()
        self.stiche = []

    def start(self):
        shuffle(self.deck.cards)
        self.deal_cards()
        return self.play()

    def deal_cards(self):
        for i, card in enumerate(self.deck.cards):
            self.players[i % 4].set_card(card=card)

    def play(self):
        start_player_index = 0
        self.trumpf = self.players[start_player_index].choose_trumpf()
        logger.info('Chosen Trumpf: {0} \n'.format(self.trumpf))
        for i in range(9):
            stich = self.play_stich(start_player_index)
            self.count_points(stich, last=(i == 8))
            logger.info('\nStich: {0} \n'.format(stich.player))
            logger.info('{}{}\n'.format('-' * 180, self.trumpf))
            start_player_index = self.players.index(stich.player)
            self.stiche.append(stich)
            if self.teams[0].won(self.point_limit) or self.teams[1].won(self.point_limit):
                return True
        return False

    def play_stich(self, start_player_index):
        first_card = self.play_card(first_card=None, player=self.players[start_player_index])
        played_cards = [PlayedCard(player=self.players[start_player_index], card=first_card)]
        for i in get_player_index(start_index=start_player_index):
            current_player = self.players[i]
            card = self.play_card(first_card=first_card, player=current_player)
            played_cards.append(PlayedCard(player=current_player, card=card))
        stich = stich_rules[self.trumpf](played_cards=played_cards)
        return stich

    def play_card(self, first_card, player):
        is_allowed_card = False
        generator = player.choose_card()
        chosen_card = next(generator)
        while not is_allowed_card:
            is_allowed_card = card_allowed(first_card=first_card, chosen_card=chosen_card, hand_cards=player.cards,
                                           trumpf=self.trumpf)
            card = generator.send(is_allowed_card)
            chosen_card = chosen_card if card is None else card
        else:
            logger.info('Table: {0}:{1}'.format(player, chosen_card))
            player.cards.remove(chosen_card)
        return chosen_card

    def count_points(self, stich, last):
        stich_player_index = self.players.index(stich.player)
        cards = [played_card.card for played_card in stich.played_cards]
        self.add_points(team_index=(stich_player_index % 2), cards=cards, last=last)

    def add_points(self, team_index, cards, last):
        self.teams[team_index].points += count_stich(cards, self.trumpf, last=last) * counting_factor[self.trumpf]


def get_player_index(start_index):
    for i in range(1, 4):
        yield (i + start_index) % 4
