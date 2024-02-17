import random
from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.main import run_game
from sc2.player import Bot, Computer

class MacroBot(BotAI):

    def __init__(self):
        # Initialize inherited class
        self.builder_sent = False
        self._1st_Pylon_Builder_Moved = False

    # pylint: disable=R0912
    async def on_step(self, iteration):
        
        # Standard TimeStamp for Action Prints
        def _print_t(add_text: str):
            print(f"i{iteration}, GTime: {self.time_formatted}:- {add_text}")
            return

        # WORKER GATHER send worker to mineral patch
        async def sendWGather(b_worker):
            b_worker.gather(self.mineral_field.closest_to(nexus), True)
            _print_t(f"return worker {b_worker.tag} back to gather")
            return

        # WORKER ENEMY - send worker to enemy base
        async def sendWEnemy(b_worker):
            e_pos = e_loc.towards(self.game_info.map_center, random.randrange(8, 15))
            b_worker.move(e_pos, True)
            _print_t(f"move worker {b_worker.tag} to Enemy Base")
            return

        # VARIABLES
        nexus = self.townhalls.random
        e_loc = self.enemy_start_locations[0]
        pylon_count = self.structures(UnitTypeId.PYLON).amount
        nexus_count = self.structures(UnitTypeId.NEXUS).amount

        # WORKER SPLIT
        if iteration == 0:
            await self.chat_send("(pylon)(nexus)(nexus)(nexus)(gg)")

            #init WORKER SPLIT
            for p in self.workers:
                p.gather(self.mineral_field.closest_to(p))
                _print_t(f"{p } Split")

        # CHRONOBOOST - If this random nexus is training a probe and has no chrono boost already, chrono it with one of the nexuses with energy
        if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and self.structures(UnitTypeId.PYLON).ready.amount >= 1:
            if nexus.energy >= 50:
                # _print_t(f"Chronoboost, energy before Chrono: {nexus.energy}")
                nexuses = self.structures(UnitTypeId.NEXUS)
                abilities = await self.get_available_abilities(nexuses)
                for loop_nexus, abilities_nexus in zip(nexuses, abilities):
                    if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                        loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                        _print_t(f"Chronoboost started, with energy {nexus.energy}")
                        break
   
        if not self.townhalls:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(e_loc)
            return   

        # PROBES - Make probes until we have 3 x 22 total
        if self.supply_workers < 66 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)

        # PYLON 1 - If we have no pylon, build one near ramp
        elif not self.structures(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.PYLON) == 0 and self.supply_used >13:
            ramp_pylon_pos = self.main_base_ramp.protoss_wall_pylon

            # move worker when we get to x minerals so that we don't waste time moving builder
            if self.minerals >= 80 and not self._1st_Pylon_Builder_Moved:
                self._1st_Pylon_Builder = self.select_build_worker(ramp_pylon_pos)
                self._1st_Pylon_Builder.move(ramp_pylon_pos)
                self._1st_Pylon_Builder_Moved = True
                _print_t(f"Init ramp Pylon builder moved, btag: {self._1st_Pylon_Builder.tag}")
                
            #Only build the pylon when we can afford it
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, ramp_pylon_pos, 0, self._1st_Pylon_Builder)
                _print_t(f"Init ramp Pylon Building, pylon count {pylon_count}")
                await sendWGather(self._1st_Pylon_Builder)


    # Do things here after the game ends
    async def on_end(self, game_result: Result):
        print(f"Game ended at {self} {game_result}")
    

def main():
    run_game(
        maps.get("Equilibrium512AIE"),
        [Bot(Race.Protoss, MacroBot(), name="OwnBot"),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        # sc2_version="5.0.12.91115",
    )


if __name__ == "__main__":
    main()