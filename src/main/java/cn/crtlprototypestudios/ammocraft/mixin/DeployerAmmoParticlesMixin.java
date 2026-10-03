package cn.crtlprototypestudios.ammocraft.mixin;

import com.simibubi.create.content.contraptions.components.deployer.BeltDeployerCallbacks;
import com.simibubi.create.content.contraptions.components.deployer.DeployerFakePlayer;
import com.simibubi.create.content.contraptions.components.deployer.DeployerTileEntity;
import com.simibubi.create.content.contraptions.relays.belt.transport.TransportedItemStack;
import com.simibubi.create.foundation.tileEntity.behaviour.belt.TransportedItemStackHandlerBehaviour;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.Recipe;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

@Mixin(BeltDeployerCallbacks.class)
public class DeployerAmmoParticlesMixin {
    @Redirect(method = "activate", at = @At(value = "FIELD", opcode = 181, target =
            "Lcom/simibubi/create/content/contraptions/components/deployer/DeployerFakePlayer;spawnedItemEffects:Lnet/minecraft/world/item/ItemStack;"),
            remap = false)
    private static void ammocraft$useMetalFragments(DeployerFakePlayer player, ItemStack original,
                                              TransportedItemStack transported,
                                              TransportedItemStackHandlerBehaviour handler,
                                              DeployerTileEntity deployer, Recipe<?> recipe) {
        // Use Create's existing one-shot particle packet and animation, but give
        // disassembly a vanilla metal sprite instead of TaCZ's custom ammo model.
        ItemStack particles = recipe.getId().getNamespace().equals("ammocraft")
                && recipe.getId().getPath().startsWith("deploying/ammo_disassembly/")
                ? new ItemStack(Items.COPPER_INGOT) : original;
        ((DeployerFakePlayerAccessor) player).ammocraft$setSpawnedItemEffects(particles);
    }
}
