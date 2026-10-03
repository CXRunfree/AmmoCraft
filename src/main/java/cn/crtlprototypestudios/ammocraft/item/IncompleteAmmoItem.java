package cn.crtlprototypestudios.ammocraft.item;

import com.simibubi.create.content.contraptions.itemAssembly.SequencedAssemblyItem;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TranslatableComponent;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

import javax.annotation.Nullable;
import java.util.List;

public class IncompleteAmmoItem extends SequencedAssemblyItem {
    public IncompleteAmmoItem(Properties properties) {
        super(properties);
    }

    @Override
    public int getItemStackLimit(ItemStack stack) {
        // The mixer outputs batches; only identical assembly NBT stacks together.
        return 64;
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(new TranslatableComponent("tooltip.ammocraft.ammo_progress", Math.round(getProgress(stack) * 100))
                .withStyle(ChatFormatting.GOLD));
    }
}
