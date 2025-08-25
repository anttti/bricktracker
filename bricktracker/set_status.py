from typing import Self

from .metadata import BrickMetadata


# Lego set status metadata
class BrickSetStatus(BrickMetadata):
    kind: str = 'status'

    # Set state endpoint
    set_state_endpoint: str = 'set.update_status'

    # Queries
    delete_query: str = 'set/metadata/status/delete'
    insert_query: str = 'set/metadata/status/insert'
    select_query: str = 'set/metadata/status/select'
    update_field_query: str = 'set/metadata/status/update/field'
    update_set_state_query: str = 'set/metadata/status/update/state'

    # Grab data from a form
    def from_form(self, form: dict[str, str], /) -> Self:
        super().from_form(form)

        grid = form.get('grid', None)

        self.fields.displayed_on_grid = grid == 'on'

        return self

    # Insert into database
    def insert(self, /, **_) -> None:
        super().insert(
            displayed_on_grid=self.fields.displayed_on_grid
        )
