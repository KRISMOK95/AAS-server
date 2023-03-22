"""Play with FastAPI and AAS."""
import logging
import threading
from typing import Any, MutableMapping, Optional, List, Union, Sequence

import uvicorn
import fastapi
import fastapi.responses

from aas_core3_rc02 import (
    types as aas_types,
    jsonization as aas_jsonization,
    verification as aas_verification
)


class Storage:
    def __init__(self) -> None:
        """Initialize with empty."""
        self.submodels = dict()  # type: MutableMapping[str, aas_types.Submodel]

        self._submodels_lock = threading.Lock()

        self.asset_administration_shells = dict(
        )  # type: MutableMapping[str, aas_types.AssetAdministrationShell]

        self._asset_administration_shells_lock = threading.Lock()

        self.concept_descriptions = dict(
        )  # type: MutableMapping[str, aas_types.ConceptDescription]

        self._concept_descriptions_lock = threading.Lock()

    def put_submodel(self, submodel: aas_types.Submodel) -> None:
        """
        Put the submodel in the storage.

        The submodels are keyed on their IDs. If the submodel with the same ID exists
        in the storage, it will be replaced.
        """
        with self._submodels_lock:
            self.submodels[submodel.id] = submodel

    def get_submodel(self, identifier: str) -> Optional[aas_types.Submodel]:
        """Try to get the submodel keyed on ``identifier`` from the storage."""
        with self._submodels_lock:
            return self.submodels.get(identifier, None)

    def list_submodels(self) -> List[str]:
        """List the identifiers of all the submodels contained on the server."""
        with self._submodels_lock:
            return sorted(self.submodels.keys())

    # TODO (mristin, 2023-03-22): implement the same for all the others

    def _get_value_only_slow(self, path: Sequence[Union[str, int]]) -> Any:
        raise NotImplementedError()

    def get_value_only(self, path: Sequence[Union[str, int]]) -> Any:
        return self._get_value_only_slow(path)


class ChillerConnection:
    def __init__(self) -> None:
        # TODO (mristin, 2023-03-22): implement some constructor
        pass

    def connect(self) -> None:
        # TODO (mristin, 2023-03-22): implement
        pass

    def close(self) -> None:
        # TODO (mristin, 2023-03-22): implement
        pass

    def get_temperature(self) -> float:
        # TODO (mristin, 2023-03-22): implement
        return 198.4

    def __enter__(self) -> "ChillerConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def float_to_xs_float(number: float) -> str:
    # TODO (mristin, 2023-03-22): implement
    return str(number)


def main() -> None:
    """Execute the main routine."""

    root_logger = logging.getLogger(f"{__name__}.{main.__name__}")

    app = fastapi.FastAPI(
        title="Playground",
        description=__doc__,
        version="1.0.0",
    )

    storage = Storage()
    storage.put_submodel(
        aas_types.Submodel(
            id_short="chiller_static",
            id="urn:zhaw:chiller_static"
        )
    )

    with ChillerConnection() as chiller_connection:
        async def get_submodel(identifier: str = fastapi.Path()) -> Any:
            submodel = storage.get_submodel(identifier)

            if submodel is not None:
                return fastapi.responses.JSONResponse(
                    content=aas_jsonization.to_jsonable(submodel)
                )

            if identifier == "urn:zhaw:chiller_runtime":
                submodel = aas_types.Submodel(
                    id=identifier,
                    id_short="chiller_runtime",
                    submodel_elements=[
                        aas_types.Property(
                            id_short="temperature",
                            value_type=aas_types.DataTypeDefXsd.FLOAT,
                            value=float_to_xs_float(
                                chiller_connection.get_temperature()
                            )
                        )
                    ]
                )

                return fastapi.responses.JSONResponse(
                    content=aas_jsonization.to_jsonable(submodel)
                )

            raise fastapi.HTTPException(
                status_code=404,
                detail=f"Submodel with the identifier {identifier!r} could not be found."
            )

        app.get("/submodels/{identifier}")(get_submodel)

        async def get_value_only(path: List[Union[str, int]] = fastapi.Body()) -> Any:
            if path == ["submodels", "chiller_runtime", "temperature"]:
                return float_to_xs_float(
                    chiller_connection.get_temperature()
                )

            raise fastapi.HTTPException(
                status_code=501,
                detail=f"We hard-coded the paths only for some of the values."
            )

        app.post("/value_only")(get_value_only)

        host = "0.0.0.0"
        port = 8080

        root_logger.info("Starting the service on: %s:%d", host, port)

        uvicorn.run(app, host=host, port=port)

    return


if __name__ == '__main__':
    main()
