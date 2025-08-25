import logging
import traceback
from typing import Self, TYPE_CHECKING

from .exceptions import ErrorException, NotFoundException
from .part_list import BrickPartList
from .rebrickable_minifigure import RebrickableMinifigure
if TYPE_CHECKING:
    from .set import BrickSet
    from .socket import BrickSocket

logger = logging.getLogger(__name__)


# Lego minifigure
class BrickMinifigure(RebrickableMinifigure):
    # Queries
    insert_query: str = 'minifigure/insert'
    generic_query: str = 'minifigure/select/generic'
    select_query: str = 'minifigure/select/specific'

    # Import a minifigure into the database
    def download(self, socket: 'BrickSocket', refresh: bool = False) -> bool:
        if self.brickset is None:
            raise ErrorException('Importing a minifigure from Rebrickable outside of a set is not supported')  # noqa: E501

        try:
            # Insert into the database
            socket.auto_progress(
                message='Set {set}: inserting minifigure {figure} into database'.format(  # noqa: E501
                    set=self.brickset.fields.set,
                    figure=self.fields.figure
                )
            )

            if not refresh:
                # Insert into database
                self.insert(commit=False)

            # Load the inventory
            if not BrickPartList.download(
                socket,
                self.brickset,
                minifigure=self,
                refresh=refresh
            ):
                return False

            # Insert the rebrickable set into database (after counting parts)
            self.insert_rebrickable()

        except Exception as e:
            socket.fail(
                message='Error while importing minifigure {figure} from {set}: {error}'.format(  # noqa: E501
                    figure=self.fields.figure,
                    set=self.brickset.fields.set,
                    error=e,
                )
            )

            logger.debug(traceback.format_exc())

            return False

        return True

    # Parts
    def generic_parts(self, /) -> BrickPartList:
        return BrickPartList().from_minifigure(self)

    # Parts
    def parts(self, /) -> BrickPartList:
        if self.brickset is None:
            raise ErrorException('Part list for minifigure {figure} requires a brickset'.format(  # noqa: E501
                figure=self.fields.figure,
            ))

        return BrickPartList().list_specific(self.brickset, minifigure=self)

    # Select a generic minifigure
    def select_generic(self, figure: str, /) -> Self:
        # Save the parameters to the fields
        self.fields.figure = figure

        if not self.select(override_query=self.generic_query):
            raise NotFoundException(
                'Minifigure with figure {figure} was not found in the database'.format(  # noqa: E501
                    figure=self.fields.figure,
                ),
            )

        return self

    # Select a specific minifigure (with a set and a figure)
    def select_specific(self, brickset: 'BrickSet', figure: str, /) -> Self:
        # Save the parameters to the fields
        self.brickset = brickset
        self.fields.figure = figure

        if not self.select():
            raise NotFoundException(
                'Minifigure with figure {figure} from set {set} was not found in the database'.format(  # noqa: E501
                    figure=self.fields.figure,
                    set=self.brickset.fields.set,
                ),
            )

        return self
