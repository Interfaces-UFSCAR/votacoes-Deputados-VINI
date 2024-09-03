class VotacaoSemVotos(Exception):
    def __init__(self):
        super().__init__('Votação sem dados dos votos')

