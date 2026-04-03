import logging
import algokit_utils

logger = logging.getLogger(__name__)


def deploy() -> None:
    from smart_contracts.artifacts.algocrefi_aura.algocrefi_aura_client import (
        AlgocrefiAuraFactory,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        AlgocrefiAuraFactory,
        default_sender=deployer.address,
    )

    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    logger.info(
        f"Aura app deployed: {app_client.app_name} ({app_client.app_id})"
    )