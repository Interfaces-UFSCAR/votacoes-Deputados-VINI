class VotacaoSemVotos(Exception):
    def __init__(self):
        super().__init__('Votação sem dados dos votos')

class ProposicaoNaoExiste(Exception):
    def __init__(self):
        super().__init__('Proposição não existe')

        