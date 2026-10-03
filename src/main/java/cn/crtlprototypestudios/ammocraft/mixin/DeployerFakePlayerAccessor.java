package cn.crtlprototypestudios.ammocraft.mixin;

import com.simibubi.create.content.contraptions.components.deployer.DeployerFakePlayer;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin(DeployerFakePlayer.class)
public interface DeployerFakePlayerAccessor {
    @Accessor(value = "spawnedItemEffects", remap = false)
    void ammocraft$setSpawnedItemEffects(ItemStack stack);
}
