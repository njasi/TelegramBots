# png to svg
import cairosvg
pieces = ["pawnw", "rookw", "knightw", "bishopw", "queenw", "kingw", "pawnb", "rookb", "knightb", "bishopb", "queenb", "kingb"]
for piece in pieces:
    cairosvg.svg2png(url="graphics/pieces/svg/{}.svg".format(piece), write_to="graphics/pieces/png/{}.png".format(piece), scale = 2)