package cn.crtlprototypestudios.ammocraft.item;

import cn.crtlprototypestudios.ammocraft.AmmoCraft;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TranslatableComponent;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

import javax.annotation.Nullable;
import java.util.List;

public class AmmoMoldItem extends Item {
    private final String ammoId;

    public AmmoMoldItem(Properties properties, String ammoId) {
        super(properties.stacksTo(1));
        this.ammoId = ammoId;
    }

    public ResourceLocation getMixingRecipeId() {
        return AmmoCraft.id("mixing/ammo_blank/" + ammoId);
    }

    @Override
    public void appendHoverText(ItemStack stack, @Nullable Level level, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(new TranslatableComponent("tooltip.ammocraft.ammo_mold")
                .withStyle(ChatFormatting.GRAY));
    }
}
