package cn.crtlprototypestudios.ammocraft.test;

import cn.crtlprototypestudios.ammocraft.registry.AmmoItems;
import cn.crtlprototypestudios.ammocraft.recipe.AmmoBlankMixingRecipe;
import com.simibubi.create.AllBlocks;
import com.simibubi.create.AllRecipeTypes;
import com.simibubi.create.content.contraptions.components.deployer.DeployerApplicationRecipe;
import com.simibubi.create.content.contraptions.components.deployer.BeltDeployerCallbacks;
import com.simibubi.create.content.contraptions.components.deployer.DeployerTileEntity;
import com.simibubi.create.content.contraptions.relays.belt.transport.TransportedItemStack;
import com.simibubi.create.foundation.tileEntity.behaviour.belt.TransportedItemStackHandlerBehaviour;
import com.simibubi.create.content.contraptions.components.press.PressingRecipe;
import com.simibubi.create.content.contraptions.itemAssembly.SequencedAssemblyRecipe;
import com.simibubi.create.content.contraptions.processing.BasinRecipe;
import com.simibubi.create.content.contraptions.processing.BasinTileEntity;
import com.simibubi.create.content.contraptions.components.mixer.MechanicalMixerTileEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraftforge.event.RegistryEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import net.minecraftforge.registries.ForgeRegistries;

import java.util.List;
import java.lang.reflect.Method;

@GameTestHolder("ammocraft")
@PrefixGameTestTemplate(false)
@Mod.EventBusSubscriber(modid = "ammocraft", bus = Mod.EventBusSubscriber.Bus.MOD)
public class AmmoPipelineTests {
    @SubscribeEvent
    public static void registerAmmo(RegistryEvent.Register<Item> event) {
        event.getRegistry().register(new Item(new Item.Properties()).setRegistryName("tacz", "ammo"));
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void mixingUsesEachMoldRecipe(GameTestHelper helper) throws ReflectiveOperationException {
        BlockPos pos = new BlockPos(1, 1, 1);
        helper.setBlock(pos, AllBlocks.BASIN.getDefaultState());
        helper.setBlock(pos.above(2), AllBlocks.MECHANICAL_MIXER.getDefaultState());
        BasinTileEntity basin = (BasinTileEntity) helper.getBlockEntity(pos);
        MechanicalMixerTileEntity mixer = (MechanicalMixerTileEntity) helper.getBlockEntity(pos.above(2));
        Method matching = MechanicalMixerTileEntity.class.getDeclaredMethod("getMatchingRecipes");
        matching.setAccessible(true);
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            clear(basin);
            Recipe<?> recipe = helper.getLevel().getRecipeManager()
                    .byKey(new ResourceLocation("ammocraft", "mixing/ammo_blank/" + caliber.id)).orElseThrow();
            check(helper, recipe instanceof AmmoBlankMixingRecipe, "Wrong blank recipe type");
            check(helper, recipe.getResultItem().is(caliber.casing.get()), "Metal must produce the independent casing");
            check(helper, recipe.getResultItem().getCount() == caliber.blanks, "Wrong blank batch size");
            check(helper, recipe.getIngredients().size() == caliber.copper + caliber.iron + caliber.ironNuggets,
                    "Wrong metal ingredient count");
            check(helper, recipe.getId().equals(caliber.mold.get().getMixingRecipeId()), "Mold recipe ID mismatch");
            basin.inputInventory.setStackInSlot(0, new ItemStack(Items.COPPER_INGOT, Math.min(caliber.copper, 64)));
            if (caliber.copper > 64) basin.inputInventory.setStackInSlot(3, new ItemStack(Items.COPPER_INGOT, Math.min(caliber.copper - 64, 64)));
            if (caliber.copper > 128) basin.inputInventory.setStackInSlot(4, new ItemStack(Items.COPPER_INGOT, caliber.copper - 128));
            if (caliber.iron > 0) basin.inputInventory.setStackInSlot(1, new ItemStack(Items.IRON_INGOT, caliber.iron));
            if (caliber.ironNuggets > 0) basin.inputInventory.setStackInSlot(2, new ItemStack(Items.IRON_NUGGET, caliber.ironNuggets));
            basin.getFilter().setFilter(ItemStack.EMPTY);
            check(helper, !BasinRecipe.match(basin, recipe), "No mold must reject ammunition mixing");
            check(helper, !BasinRecipe.apply(basin, recipe), "Direct application must also require a mold");
            basin.getFilter().setFilter(new ItemStack(caliber.casing.get()));
            check(helper, !BasinRecipe.match(basin, recipe), "Filtering the output cannot bypass the mold");
            basin.getFilter().setFilter(new ItemStack(caliber.mold.get()));
            check(helper, BasinRecipe.match(basin, recipe), "Correct mold must accept exact materials: " + caliber.id);
            List<?> selected = (List<?>) matching.invoke(mixer);
            check(helper, selected.size() == 1 && ((Recipe<?>) selected.get(0)).getId().equals(recipe.getId()),
                    "Mixer must select exactly the mold's recipe");
            check(helper, BasinRecipe.apply(basin, recipe), "Mixing application failed: " + caliber.id);
            check(helper, basin.inputInventory.isEmpty(), "All exact metal inputs must be consumed");
            int output = 0;
            for (int slot = 0; slot < basin.getOutputInventory().getSlots(); slot++) {
                ItemStack stack = basin.getOutputInventory().getStackInSlot(slot);
                if (stack.is(caliber.casing.get())) output += stack.getCount();
            }
            check(helper, output == caliber.blanks, "Batch output lost items");
            check(helper, basin.getFilter().getFilter().is(caliber.mold.get()), "Mold must remain in filter");
            clear(basin);
            if (caliber.copper > 1)
                basin.inputInventory.setStackInSlot(0, new ItemStack(Items.COPPER_INGOT, Math.min(caliber.copper - 1, 64)));
            if (caliber.copper > 65) basin.inputInventory.setStackInSlot(3, new ItemStack(Items.COPPER_INGOT, Math.min(caliber.copper - 65, 64)));
            if (caliber.copper > 129) basin.inputInventory.setStackInSlot(4, new ItemStack(Items.COPPER_INGOT, caliber.copper - 129));
            if (caliber.iron > 0) basin.inputInventory.setStackInSlot(1, new ItemStack(Items.IRON_INGOT, caliber.iron));
            if (caliber.ironNuggets > 0) basin.inputInventory.setStackInSlot(2, new ItemStack(Items.IRON_NUGGET, caliber.ironNuggets));
            check(helper, !BasinRecipe.match(basin, recipe), "Insufficient copper must be rejected");
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void casingOverflowRetriesOutput(GameTestHelper helper) {
        BlockPos pos = new BlockPos(1, 2, 1);
        helper.setBlock(pos, AllBlocks.BASIN.getDefaultState().setValue(
                com.simibubi.create.content.contraptions.processing.BasinBlock.FACING, net.minecraft.core.Direction.EAST));
        helper.setBlock(pos.east().below(), AllBlocks.DEPOT.getDefaultState());
        BasinTileEntity basin = (BasinTileEntity) helper.getBlockEntity(pos);
        var receiver = helper.getBlockEntity(pos.east().below()).getCapability(
                net.minecraftforge.items.CapabilityItemHandler.ITEM_HANDLER_CAPABILITY).orElseThrow(IllegalStateException::new);
        AmmoItems.Caliber caliber = AmmoItems.CALIBERS.get(0);
        // Reproduce a full stack plus the reported stranded twelve-round batch.
        basin.getOutputInventory().setStackInSlot(0, new ItemStack(caliber.casing.get(), 64));
        basin.getOutputInventory().setStackInSlot(1, new ItemStack(caliber.casing.get(), 12));
        receiver.insertItem(0, new ItemStack(Items.COBBLESTONE, 64), false);
        for (int tick = 0; tick < 3; tick++) basin.tick();
        int received = 0;
        receiver.extractItem(0, 64, false);
        for (int tick = 0; tick < 12; tick++) {
            basin.tick();
            for (int slot = 0; slot < receiver.getSlots(); slot++) {
                ItemStack extracted = receiver.extractItem(slot, 64, false);
                if (extracted.is(caliber.casing.get())) received += extracted.getCount();
            }
        }
        check(helper, received == 76, "Must retry output after blockage: expected 76, got " + received);
        check(helper, basin.getOutputInventory().isEmpty(), "The extra 12 casings must not remain stranded");
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void bulkCasingManufacturingWaitsForOutput(GameTestHelper helper) {
        BlockPos pos = new BlockPos(1, 2, 1);
        helper.setBlock(pos, AllBlocks.BASIN.getDefaultState().setValue(
                com.simibubi.create.content.contraptions.processing.BasinBlock.FACING, net.minecraft.core.Direction.EAST));
        helper.setBlock(pos.east().below(), AllBlocks.DEPOT.getDefaultState());
        BasinTileEntity basin = (BasinTileEntity) helper.getBlockEntity(pos);
        var receiver = helper.getBlockEntity(pos.east().below()).getCapability(
                net.minecraftforge.items.CapabilityItemHandler.ITEM_HANDLER_CAPABILITY).orElseThrow(IllegalStateException::new);
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            clear(basin);
            basin.getFilter().setFilter(new ItemStack(caliber.mold.get()));
            int batches = Math.min(8, 64 / caliber.copper);
            // Seed the large stacks reported by the player directly; automated
            // insertion has a separate 16-item-per-material limit in Create.
            basin.inputInventory.setStackInSlot(0, new ItemStack(Items.COPPER_INGOT, caliber.copper * batches));
            if (caliber.iron > 0)
                basin.inputInventory.setStackInSlot(1, new ItemStack(Items.IRON_INGOT, caliber.iron * batches));
            if (caliber.ironNuggets > 0)
                basin.inputInventory.setStackInSlot(2, new ItemStack(Items.IRON_NUGGET, caliber.ironNuggets * batches));
            Recipe<?> recipe = helper.getLevel().getRecipeManager().byKey(
                    new ResourceLocation("ammocraft", "mixing/ammo_blank/" + caliber.id)).orElseThrow();
            int received = 0;
            for (int batch = 0; batch < batches; batch++) {
                check(helper, BasinRecipe.apply(basin, recipe), "Next casing batch must resume after output clears");
                for (int tick = 0; tick < 3; tick++) basin.tick();
                for (int slot = 0; slot < receiver.getSlots(); slot++) {
                    ItemStack output = receiver.extractItem(slot, 64, false);
                    check(helper, output.isEmpty() || (output.is(caliber.casing.get()) && output.getCount() <= 64),
                            "Receiver must get legal casing stacks");
                    received += output.getCount();
                }
            }
            check(helper, received == batches * caliber.blanks, "Bulk output count mismatch: " + caliber.id);
            check(helper, basin.inputInventory.isEmpty(), "Exactly the supplied batches of metal must be consumed");
            check(helper, basin.getOutputInventory().isEmpty(), "No casings may remain stranded");
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void casingCapacityRequiresWholeBatch(GameTestHelper helper) {
        BlockPos pos = new BlockPos(1, 2, 1);
        helper.setBlock(pos, AllBlocks.BASIN.getDefaultState().setValue(
                com.simibubi.create.content.contraptions.processing.BasinBlock.FACING, net.minecraft.core.Direction.EAST));
        helper.setBlock(pos.east().below(), AllBlocks.DEPOT.getDefaultState());
        BasinTileEntity basin = (BasinTileEntity) helper.getBlockEntity(pos);
        var receiver = helper.getBlockEntity(pos.east().below()).getCapability(
                net.minecraftforge.items.CapabilityItemHandler.ITEM_HANDLER_CAPABILITY).orElseThrow(IllegalStateException::new);
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            clear(basin);
            basin.getFilter().setFilter(new ItemStack(caliber.mold.get()));
            basin.inputInventory.setStackInSlot(0, new ItemStack(Items.COPPER_INGOT, caliber.copper * 2));
            if (caliber.iron > 0)
                basin.inputInventory.setStackInSlot(1, new ItemStack(Items.IRON_INGOT, caliber.iron * 2));
            basin.getOutputInventory().setStackInSlot(0, new ItemStack(caliber.casing.get(), 60 - caliber.blanks));
            Recipe<?> recipe = helper.getLevel().getRecipeManager().byKey(
                    new ResourceLocation("ammocraft", "mixing/ammo_blank/" + caliber.id)).orElseThrow();
            check(helper, BasinRecipe.match(basin, recipe), "Exactly one batch of free space must allow production");
            check(helper, BasinRecipe.apply(basin, recipe), "Existing casings must not block a fitting batch");
            CompoundTag before = basin.inputInventory.serializeNBT();
            check(helper, !BasinRecipe.match(basin, recipe) && !BasinRecipe.apply(basin, recipe),
                    "Combined inventory and queued output must not exceed 60");
            check(helper, before.equals(basin.inputInventory.serializeNBT()), "Capacity rejection must preserve input");
            for (int tick = 0; tick < 4; tick++) basin.tick();
            int received = 0;
            for (int slot = 0; slot < receiver.getSlots(); slot++)
                received += receiver.extractItem(slot, 64, false).getCount();
            // A depot may wait for its current stack to be removed before accepting the next.
            for (int tick = 0; tick < 4; tick++) basin.tick();
            for (int slot = 0; slot < receiver.getSlots(); slot++)
                received += receiver.extractItem(slot, 64, false).getCount();
            check(helper, received == 60, "Capacity-bound output must preserve exactly 60 casings");
            check(helper, BasinRecipe.match(basin, recipe), "Production must resume after output clears");
            basin.getOutputInventory().setStackInSlot(0, new ItemStack(caliber.casing.get(), 61 - caliber.blanks));
            before = basin.inputInventory.serializeNBT();
            check(helper, !BasinRecipe.match(basin, recipe) && !BasinRecipe.apply(basin, recipe),
                    "One less than a full batch of free space must reject production");
            check(helper, before.equals(basin.inputInventory.serializeNBT()), "Partial room must not consume input");
            basin.getOutputInventory().setStackInSlot(0, ItemStack.EMPTY);
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void disassemblyAndMoldsExist(GameTestHelper helper) {
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            Recipe<?> disassembly = helper.getLevel().getRecipeManager()
                    .byKey(new ResourceLocation("ammocraft", "deploying/ammo_disassembly/" + caliber.id)).orElseThrow();
            DeployerApplicationRecipe dismantling = (DeployerApplicationRecipe) disassembly;
            ItemStack sample = ammo(caliber.id);
            sample.getOrCreateTag().putInt("Extra", 7);
            check(helper, disassembly.getIngredients().get(0).test(sample), "Extra ammo NBT must be accepted");
            check(helper, !disassembly.getIngredients().get(0).test(ammo("wrong")), "Wrong caliber cannot be dismantled");
            check(helper, dismantling.getRequiredHeldItem().test(new ItemStack(AmmoItems.DISASSEMBLY_TOOL.get())), "Pliers missing");
            check(helper, dismantling.shouldKeepHeldItem(), "Pliers must not be consumed");
            check(helper, disassembly.getResultItem().is(caliber.powder.get()), "Wrong powder result");
            check(helper, helper.getLevel().getRecipeManager()
                    .byKey(new ResourceLocation("ammocraft", "deploying/powder_formula/" + caliber.id)).isEmpty(),
                    "Recording recipe must be removed");
            DeployerApplicationRecipe engraving = (DeployerApplicationRecipe) helper.getLevel().getRecipeManager()
                    .byKey(new ResourceLocation("ammocraft", "deploying/ammo_mold/" + caliber.id)).orElseThrow();
            check(helper, engraving.getRequiredHeldItem().test(sample) && engraving.shouldKeepHeldItem(),
                    "Mold engraving must retain the matching ammo sample");
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void disassemblyEmitsMetalParticles(GameTestHelper helper) {
        BlockPos pos = new BlockPos(1, 3, 1);
        helper.setBlock(pos, AllBlocks.DEPLOYER.getDefaultState());
        helper.runAfterDelay(2, () -> {
            DeployerTileEntity deployer = (DeployerTileEntity) helper.getBlockEntity(pos);
            check(helper, deployer.getPlayer() != null, "Deployer player must initialize");
            for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
                Recipe<?> recipe = helper.getLevel().getRecipeManager().byKey(
                        new ResourceLocation("ammocraft", "deploying/ammo_disassembly/" + caliber.id)).orElseThrow();
                deployer.getPlayer().setItemInHand(InteractionHand.MAIN_HAND,
                        new ItemStack(AmmoItems.DISASSEMBLY_TOOL.get()));
                TransportedItemStack input = new TransportedItemStack(ammo(caliber.id));
                CompoundTag packet = new CompoundTag();
                TransportedItemStackHandlerBehaviour handler = new TransportedItemStackHandlerBehaviour(
                        deployer, (position, processing) -> {
                    var result = processing.apply(input);
                    check(helper, result.getOutputs().size() == 1
                                    && result.getOutputs().get(0).stack.is(caliber.powder.get())
                                    && result.getOutputs().get(0).stack.getCount() == 1,
                            "Metal effects must preserve disassembly output");
                    deployer.write(packet, true);
                });
                BeltDeployerCallbacks.activate(input, handler, deployer, recipe);
                check(helper, ItemStack.of(packet.getCompound("Particle")).is(Items.COPPER_INGOT),
                        "Disassembly must sync copper fragments: " + caliber.id);
                check(helper, deployer.getPlayer().getMainHandItem().is(AmmoItems.DISASSEMBLY_TOOL.get()),
                        "Particle effect must not consume the pliers");
                CompoundTag nextPacket = new CompoundTag();
                deployer.write(nextPacket, true);
                check(helper, !nextPacket.contains("Particle"), "Particles must only emit once per operation");
            }
            AmmoItems.Caliber caliber = AmmoItems.CALIBERS.get(0);
            Recipe<?> engraving = helper.getLevel().getRecipeManager().byKey(
                    new ResourceLocation("ammocraft", "deploying/ammo_mold/" + caliber.id)).orElseThrow();
            deployer.getPlayer().setItemInHand(InteractionHand.MAIN_HAND, ammo(caliber.id));
            TransportedItemStack input = new TransportedItemStack(new ItemStack(AmmoItems.BLANK_MOLD.get()));
            CompoundTag packet = new CompoundTag();
            TransportedItemStackHandlerBehaviour handler = new TransportedItemStackHandlerBehaviour(
                    deployer, (position, processing) -> {
                processing.apply(input);
                deployer.write(packet, true);
            });
            BeltDeployerCallbacks.activate(input, handler, deployer, engraving);
            check(helper, ItemStack.of(packet.getCompound("Particle")).is(AmmoItems.BLANK_MOLD.get()),
                    "Other deployer recipes must retain their original particles");
            helper.succeed();
        });
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void assemblyUsesCaliberPowder(GameTestHelper helper) {
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            ItemStack blank = new ItemStack(caliber.casing.get());
            check(helper, !(blank.getItem() instanceof com.simibubi.create.content.contraptions.itemAssembly.SequencedAssemblyItem),
                    "Casing must be an independent plain item");
            check(helper, blank.getMaxStackSize() == 64, "Casings must stack to 64");
            check(helper, SequencedAssemblyRecipe.getRecipe(helper.getLevel(), new ItemStack(caliber.incomplete.get()),
                    AllRecipeTypes.DEPLOYING.getType(), DeployerApplicationRecipe.class).isEmpty(),
                    "Uninitialized incomplete ammo must not bypass the casing input");
            check(helper, SequencedAssemblyRecipe.getRecipe(helper.getLevel(), blank,
                    AllRecipeTypes.PRESSING.getType(), PressingRecipe.class).isEmpty(), "Cannot press before powder");
            DeployerApplicationRecipe powder = SequencedAssemblyRecipe.getRecipe(helper.getLevel(), blank,
                    AllRecipeTypes.DEPLOYING.getType(), DeployerApplicationRecipe.class).orElseThrow();
            check(helper, powder.getRequiredHeldItem().test(new ItemStack(caliber.powder.get())), "Wrong powder input");
            check(helper, !powder.getRequiredHeldItem().test(new ItemStack(Items.GUNPOWDER)), "Raw powder cannot replace caliber powder");
            AmmoItems.Caliber other = AmmoItems.CALIBERS.get((AmmoItems.CALIBERS.indexOf(caliber) + 1) % AmmoItems.CALIBERS.size());
            check(helper, !powder.getRequiredHeldItem().test(new ItemStack(other.powder.get())), "Wrong caliber powder accepted");
            ItemStack loaded = powder.rollResults().get(0);
            check(helper, loaded.is(caliber.incomplete.get()) && loaded.getCount() == 1,
                    "Loading one casing must transition to one incomplete round");
            float loadedProgress = caliber.id.equals("12g") ? 1f / 3 : 0.5f;
            check(helper, Math.abs(caliber.incomplete.get().getProgress(loaded) - loadedProgress) < 0.001f, "Wrong loaded progress");
            if (caliber.id.equals("12g")) {
                check(helper, SequencedAssemblyRecipe.getRecipe(helper.getLevel(), loaded,
                        AllRecipeTypes.PRESSING.getType(), PressingRecipe.class).isEmpty(), "12g cannot press before pellet filling");
                DeployerApplicationRecipe pellets = SequencedAssemblyRecipe.getRecipe(helper.getLevel(), loaded,
                        AllRecipeTypes.DEPLOYING.getType(), DeployerApplicationRecipe.class).orElseThrow();
                check(helper, pellets.getRequiredHeldItem().test(new ItemStack(Items.IRON_NUGGET)), "12g requires one iron nugget");
                check(helper, !pellets.getRequiredHeldItem().test(new ItemStack(Items.IRON_INGOT)), "Iron ingot cannot replace nugget");
                check(helper, !pellets.shouldKeepHeldItem(), "Iron nugget must be consumed");
                loaded = pellets.rollResults().get(0);
                check(helper, Math.abs(caliber.incomplete.get().getProgress(loaded) - 2f / 3) < 0.001f, "12g pellet progress must be two thirds");
            }
            PressingRecipe pressing = SequencedAssemblyRecipe.getRecipe(helper.getLevel(), loaded,
                    AllRecipeTypes.PRESSING.getType(), PressingRecipe.class).orElseThrow();
            ItemStack finished = pressing.rollResults().get(0);
            check(helper, finished.is(ForgeRegistries.ITEMS.getValue(new ResourceLocation("tacz", "ammo"))), "Wrong final item");
            check(helper, finished.getCount() == 1, "One blank makes one round");
            check(helper, finished.getOrCreateTag().getString("AmmoId").equals("tacz:" + caliber.id), "Wrong final caliber");
            check(helper, !finished.getOrCreateTag().contains("SequencedAssembly"), "Final ammo retains progress NBT");
        }
        helper.succeed();
    }

    @GameTest(template = "empty", timeoutTicks = 100)
    public static void commonIngredientsRemainAvailable(GameTestHelper helper) throws ReflectiveOperationException {
        Recipe<?> lapisPressing = helper.getLevel().getRecipeManager()
                .byKey(new ResourceLocation("ammocraft", "pressing/lapis_dust")).orElseThrow();
        check(helper, lapisPressing instanceof PressingRecipe, "Lapis dust must use the mechanical press");
        check(helper, lapisPressing.getIngredients().size() == 1
                && lapisPressing.getIngredients().get(0).test(new ItemStack(Items.LAPIS_LAZULI)), "Press requires one lapis");
        check(helper, lapisPressing.getResultItem().is(AmmoItems.LAPIS_DUST.get())
                && lapisPressing.getResultItem().getCount() == 1, "Press must make one AmmoCraft lapis dust");
        for (String removed : List.of("common_propellant", "concentrated_propellant", "lapis_additive"))
            check(helper, helper.getLevel().getRecipeManager().byKey(new ResourceLocation("ammocraft", "crafting/" + removed)).isEmpty(),
                    "Compressed charge recipe must be removed");
        check(helper, helper.getLevel().getRecipeManager().byKey(new ResourceLocation("ammocraft", "crafting/ammo_disassembly_tool")).isPresent(),
                "Disassembly pliers recipe missing");
        BlockPos pos = new BlockPos(1, 1, 1);
        helper.setBlock(pos, AllBlocks.BASIN.getDefaultState());
        helper.setBlock(pos.above(2), AllBlocks.MECHANICAL_MIXER.getDefaultState());
        BasinTileEntity basin = (BasinTileEntity) helper.getBlockEntity(pos);
        MechanicalMixerTileEntity mixer = (MechanicalMixerTileEntity) helper.getBlockEntity(pos.above(2));
        Method matching = MechanicalMixerTileEntity.class.getDeclaredMethod("getMatchingRecipes");
        matching.setAccessible(true);
        for (AmmoItems.Caliber caliber : AmmoItems.CALIBERS) {
            clear(basin);
            Recipe<?> recipe = helper.getLevel().getRecipeManager()
                    .byKey(new ResourceLocation("ammocraft", "mixing/ammo_powder/" + caliber.id)).orElseThrow();
            check(helper, recipe.getType() == AllRecipeTypes.MIXING.getType(), "Powder must require mixing");
            check(helper, helper.getLevel().getRecipeManager().getRecipes().stream()
                    .noneMatch(r -> r instanceof CraftingRecipe && r.getResultItem().is(caliber.powder.get())),
                    "Caliber powder must have no crafting recipe");
            for (int i = 0; i < recipe.getIngredients().size(); i++) {
                ItemStack input = recipe.getIngredients().get(i).getItems()[0].copy();
                for (int slot = 0; slot < basin.inputInventory.getSlots() && !input.isEmpty(); slot++)
                    input = basin.inputInventory.insertItem(slot, input, false);
                check(helper, input.isEmpty(), "Raw powder inputs must fit stacked basin slots");
            }
            basin.getFilter().setFilter(ItemStack.EMPTY);
            check(helper, !BasinRecipe.match(basin, recipe), "Powder requires caliber powder selection");
            check(helper, !BasinRecipe.apply(basin, recipe), "Direct mixing cannot bypass caliber selection");
            basin.getFilter().setFilter(new ItemStack(Items.PAPER));
            check(helper, !BasinRecipe.match(basin, recipe), "Plain paper cannot select caliber");
            AmmoItems.Caliber other = AmmoItems.CALIBERS.get((AmmoItems.CALIBERS.indexOf(caliber) + 1) % AmmoItems.CALIBERS.size());
            basin.getFilter().setFilter(new ItemStack(other.powder.get()));
            check(helper, !BasinRecipe.match(basin, recipe), "Wrong caliber powder accepted");
            basin.getFilter().setFilter(new ItemStack(caliber.powder.get()));
            check(helper, BasinRecipe.match(basin, recipe), "Correct powder does not match: " + caliber.id);
            List<?> selected = (List<?>) matching.invoke(mixer);
            check(helper, selected.size() == 1 && ((Recipe<?>) selected.get(0)).getId().equals(recipe.getId()),
                    "Mixer must select exactly the caliber powder's recipe");
            check(helper, BasinRecipe.apply(basin, recipe), "Powder mixing failed");
            check(helper, basin.inputInventory.isEmpty(), "Powder inputs must be consumed exactly");
            int output = 0;
            for (int slot = 0; slot < basin.getOutputInventory().getSlots(); slot++) {
                ItemStack stack = basin.getOutputInventory().getStackInSlot(slot);
                if (stack.is(caliber.powder.get())) output += stack.getCount();
            }
            check(helper, output == caliber.doses, "Wrong powder batch");
            check(helper, basin.getFilter().getFilter().is(caliber.powder.get()), "Powder sample must remain in filter");
        }
        for (ResourceLocation id : ForgeRegistries.ITEMS.getKeys()) {
            if (id.getNamespace().equals("ammocraft")) {
                String path = id.getPath();
                check(helper, !(path.endsWith("_head") || path.endsWith("_casing") || path.endsWith("_transition")
                        || path.contains("gunpowder_cartridge") || path.endsWith("ammunition_gunpowder")
                         || path.startsWith("shotgun_") || path.startsWith("powder_formula_")
                          || path.equals("cartridge_primer") || path.equals("40mm_slug")
                          || List.of("common_propellant", "concentrated_propellant", "lapis_additive").contains(path)),
                        "Legacy ammunition item remains registered: " + path);
            }
        }
        helper.succeed();
    }

    private static void clear(BasinTileEntity basin) {
        for (int i = 0; i < basin.inputInventory.getSlots(); i++) basin.inputInventory.setStackInSlot(i, ItemStack.EMPTY);
        for (int i = 0; i < basin.getOutputInventory().getSlots(); i++) basin.getOutputInventory().setStackInSlot(i, ItemStack.EMPTY);
    }

    private static ItemStack ammo(String id) {
        ItemStack stack = new ItemStack(ForgeRegistries.ITEMS.getValue(new ResourceLocation("tacz", "ammo")));
        stack.getOrCreateTag().putString("AmmoId", "tacz:" + id);
        return stack;
    }

    private static void check(GameTestHelper helper, boolean condition, String message) {
        if (!condition)
            helper.fail(message);
    }
}
