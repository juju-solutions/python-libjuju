import pytest

from .. import base


@base.bootstrapped
@pytest.mark.asyncio
async def test_offer(event_loop):
    async with base.CleanModel() as model:
        application = await model.deploy(
            'cs:~jameinel/ubuntu-lite-7',
            application_name='ubuntu',
            series='bionic',
            channel='stable',
        )
        assert 'ubuntu' in model.applications
        await model.block_until(
            lambda: all(unit.workload_status == 'active'
                        for unit in application.units))
        await model.create_offer("ubuntu:ubuntu")

        offers = await model.list_offers()
        await model.block_until(
            lambda: all(offer.application_name == 'ubuntu'
                        for offer in offers.results))
        await model.remove_offer("admin/{}.ubuntu".format(model.info.name), force=True)


@base.bootstrapped
@pytest.mark.asyncio
async def test_consume(event_loop):
    async with base.CleanModel() as model_1:
        application = await model_1.deploy(
            'cs:~jameinel/ubuntu-lite-7',
            application_name='ubuntu',
            series='bionic',
            channel='stable',
        )
        assert 'ubuntu' in model_1.applications
        await model_1.block_until(
            lambda: all(unit.workload_status == 'active'
                        for unit in application.units))
        await model_1.create_offer("ubuntu:ubuntu")

        offers = await model_1.list_offers()
        await model_1.block_until(
            lambda: all(offer.application_name == 'ubuntu'
                        for offer in offers.results))

        # farm off a new model to test the consumption
        async with base.CleanModel() as model_2:
            await model_2.consume("admin/{}.ubuntu".format(model_1.info.name))

            status = await model_2.get_status()
            if 'ubuntu' not in status.remote_applications:
                raise Exception("Expected ubuntu in saas")

        await model_1.remove_offer("admin/{}.ubuntu".format(model_1.info.name), force=True)


@base.bootstrapped
@pytest.mark.asyncio
async def test_remove_saas(event_loop):
    async with base.CleanModel() as model_1:
        application = await model_1.deploy(
            'cs:~jameinel/ubuntu-lite-7',
            application_name='ubuntu',
            series='bionic',
            channel='stable',
        )
        assert 'ubuntu' in model_1.applications
        await model_1.block_until(
            lambda: all(unit.workload_status == 'active'
                        for unit in application.units))
        await model_1.create_offer("ubuntu:ubuntu")

        offers = await model_1.list_offers()
        await model_1.block_until(
            lambda: all(offer.application_name == 'ubuntu'
                        for offer in offers.results))

        # farm off a new model to test the consumption
        async with base.CleanModel() as model_2:
            await model_2.consume("admin/{}.ubuntu".format(model_1.info.name))

            status = await model_2.get_status()
            if 'ubuntu' not in status.remote_applications:
                raise Exception("Expected ubuntu in saas")

            await model_2.remove_saas('ubuntu')

            status = await model_2.get_status()
            if 'ubuntu' in status.remote_applications:
                raise Exception("Expected ubuntu not to be in saas")

        await model_1.remove_offer("admin/{}.ubuntu".format(model_1.info.name), force=True)


@base.bootstrapped
@pytest.mark.asyncio
async def test_add_relation_with_offer(event_loop):
    async with base.CleanModel() as model_1:
        application = await model_1.deploy(
            'cs:~jameinel/ubuntu-lite-7',
            application_name='ubuntu',
            series='bionic',
            channel='stable',
        )
        assert 'ubuntu' in model_1.applications
        await model_1.block_until(
            lambda: all(unit.workload_status == 'active'
                        for unit in application.units))
        await model_1.create_offer("ubuntu:ubuntu")

        offers = await model_1.list_offers()
        await model_1.block_until(
            lambda: all(offer.application_name == 'ubuntu'
                        for offer in offers.results))

        # farm off a new model to test the consumption
        async with base.CleanModel() as model_2:
            await model_2.deploy(
                'nrpe',
                application_name='nrpe',
                series='trusty',
                channel='stable',
                # subordinates must be deployed without units
                num_units=0,
            )
            await model_2.block_until(
                lambda: all(unit.workload_status == 'active'
                            for unit in application.units))

            await model_2.add_relation("admin/{}.ubuntu".format(model_1.info.name), 'nrpe')

            status = await model_2.get_status()
            if 'ubuntu' not in status.remote_applications:
                raise Exception("Expected ubuntu in saas")

            await model_2.remove_saas('ubuntu')

            status = await model_2.get_status()
            if 'ubuntu' in status.remote_applications:
                raise Exception("Expected ubuntu not to be in saas")

        await model_1.remove_offer("admin/{}.ubuntu".format(model_1.info.name), force=True)
