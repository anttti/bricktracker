import logging
import traceback
from typing import Any, Self, TYPE_CHECKING

from flask import current_app

from .minifigure import BrickMinifigure
from .rebrickable import Rebrickable
from .record_list import BrickRecordList
if TYPE_CHECKING:
    from .set import BrickSet
    from .socket import BrickSocket

logger = logging.getLogger(__name__)


# Lego minifigures
class BrickMinifigureList(BrickRecordList[BrickMinifigure]):
    brickset: 'BrickSet | None'
    order: str

    # Queries
    all_query: str = 'minifigure/list/all'
    damaged_part_query: str = 'minifigure/list/damaged_part'
    last_query: str = 'minifigure/list/last'
    missing_part_query: str = 'minifigure/list/missing_part'
    select_query: str = 'minifigure/list/from_set'
    using_part_query: str = 'minifigure/list/using_part'

    def __init__(self, /):
        super().__init__()

        # Placeholders
        self.brickset = None

        # Store the order for this list
        self.order = current_app.config['MINIFIGURES_DEFAULT_ORDER']

    # Load all minifigures
    def all(self, /) -> Self:
        self.list(override_query=self.all_query)

        return self

    # Minifigures with a part damaged part
    def damaged_part(self, part: str, color: int, /) -> Self:
        # Save the parameters to the fields
        self.fields.part = part
        self.fields.color = color

        # Load the minifigures from the database
        self.list(override_query=self.damaged_part_query)

        return self

    # Last added minifigure
    def last(self, /, *, limit: int = 6) -> Self:
        # Randomize
        if current_app.config['RANDOM']:
            order = 'RANDOM()'
        else:
            order = '"bricktracker_minifigures"."rowid" DESC'

        self.list(override_query=self.last_query, order=order, limit=limit)

        return self

    # Base minifigure list
    def list(
        self,
        /,
        *,
        override_query: str | None = None,
        order: str | None = None,
        limit: int | None = None,
        **context: Any,
    ) -> None:
        if order is None:
            order = self.order

        if hasattr(self, 'brickset'):
            brickset = self.brickset
        else:
            brickset = None

        # Load the sets from the database
        for record in super().select(
            override_query=override_query,
            order=order,
            limit=limit,
        ):
            minifigure = BrickMinifigure(brickset=brickset, record=record)

            self.records.append(minifigure)

    # Load minifigures from a brickset
    def from_set(self, brickset: 'BrickSet', /) -> Self:
        # Save the brickset
        self.brickset = brickset

        # Load the minifigures from the database
        self.list()

        return self

    # Minifigures missing a part
    def missing_part(self, part: str, color: int, /) -> Self:
        # Save the parameters to the fields
        self.fields.part = part
        self.fields.color = color

        # Load the minifigures from the database
        self.list(override_query=self.missing_part_query)

        return self

    # Minifigure using a part
    def using_part(self, part: str, color: int, /) -> Self:
        # Save the parameters to the fields
        self.fields.part = part
        self.fields.color = color

        # Load the minifigures from the database
        self.list(override_query=self.using_part_query)

        return self

    # Return a dict with common SQL parameters for a minifigures list
    def sql_parameters(self, /) -> dict[str, Any]:
        parameters: dict[str, Any] = super().sql_parameters()

        if self.brickset is not None:
            parameters['id'] = self.brickset.fields.id

        return parameters

    # Import the minifigures from Rebrickable
    @staticmethod
    def download(
        socket: 'BrickSocket',
        brickset: 'BrickSet',
        /,
        *,
        refresh: bool = False
    ) -> bool:
        try:
            socket.auto_progress(
                message='Set {set}: loading minifigures from Rebrickable'.format(  # noqa: E501
                    set=brickset.fields.set,
                ),
                increment_total=True,
            )

            logger.debug('rebrick.lego.get_set_minifigs("{set}")'.format(
                set=brickset.fields.set,
            ))

            minifigures = Rebrickable[BrickMinifigure](
                'get_set_minifigs',
                brickset.fields.set,
                BrickMinifigure,
                socket=socket,
                brickset=brickset,
            ).list()

            # Process each minifigure
            for minifigure in minifigures:
                if not minifigure.download(socket, refresh=refresh):
                    return False

            return True

        except Exception as e:
            socket.fail(
                message='Error while importing set {set} minifigure list: {error}'.format(  # noqa: E501
                    set=brickset.fields.set,
                    error=e,
                )
            )

            logger.debug(traceback.format_exc())

            return False
