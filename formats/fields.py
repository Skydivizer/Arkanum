from formats.helpers import FileStruct

sint_parser = FileStruct("<i")

byte_parser =  FileStruct("<B")
int_parser = FileStruct("<I")
long_parser = FileStruct("<Q")

class ByteParser(object):
    parser = byte_parser

    @classmethod
    def read_from(cls, file):

        return cls.parser.unpack_from_file(file)[0]

    @classmethod
    def write_to(cls, file, data):

        cls.parser.pack_into_file(file, (data))

class DefaultParser(object):
    parser = sint_parser

    @classmethod
    def read_from(cls, file):

        return cls.parser.unpack_from_file(file)[0]

    @classmethod
    def write_to(cls, file, data):

        cls.parser.pack_into_file(file, (data))

class PositionParser(object):
    exists_parser = byte_parser
    parser = FileStruct("<2I")

    @classmethod
    def read_from(cls, file):

        exists = cls.exists_parser.unpack_from_file(file)[0]

        if exists:
            return cls.parser.unpack_from_file(file)

        else:
            return None

    @classmethod
    def write_to(cls, file, data):

        if data:
            cls.exists_parser.pack_into_file(file, (1))
            cls.parser.pack_into_file(data)

        else:
            cls.exists_parser.pack_into_file(file, (0))


class ArrayParser(object):
    "Array fields have a variable number of elements of a given size."
    exists_parser = byte_parser
    header_parser = FileStruct("<3I")
    flags_size_format = "I"

    @classmethod
    def read_from(cls, file):

        exists = cls.exists_parser.unpack_from_file(file)[0]

        if exists:
            # _1 List ID(?)
            element_size, element_count, _1 = cls.header_parser.unpack_from_file(file)

            # Unpack array + flag size
            array_format = ("%ds" % element_size) * element_count
            unpacked = FileStruct("<" + array_format + cls.flags_size_format).unpack_from_file(file)
            array = unpacked[:-1]
            flags_size = unpacked[-1]

            # Unpack flags
            raw_flags = FileStruct("<%dB"% (flags_size * 4)).unpack_from_file(file)
            flags = int.from_bytes(raw_flags, 'little')

            return _1, array, flags, flags_size

        else:
            return None

    @classmethod
    def write_to(cls, file, data):

        if data:
            cls.exists_parser.pack_into_file(file, (1))

            _1, array, flags, flags_size = data
            element_count = len(array)
            element_size = len(array[0])

            cls.header_parser.pack_into_file(file, (element_size, element_count, _1))
            
            array_format = ("%ds" % element_size) * element_count
            flags_format = "<%dB"% (flags_size * 4)
            FileStruct("<" + array_format + flags_size_format + flags_format).pack_into_file(file, (*array, flags_size, *flags))

        else:
            cls.exists_parser.pack_into_file(file, (0))


class StringParser(object):
    exists_parser = byte_parser
    size_parser = int_parser
    size_fmt = "I"

    @classmethod
    def read_from(cls, file):

        exists, = cls.exists_parser.unpack_from_file(file)

        if exists:
            size, = cls.size_parser.unpack_from_file(file)

            string = FileStruct("%ds" % (size + 1)).unpack_from_file(file)

            return string

        else:
            return None

    @classmethod
    def write_to(cls, file, data):
        if data:
            cls.exists_parser.pack_into_file(file, (1))

            size = len(data) - 1

            string_fmt = "%ds" % (size + 1)

            FileStruct("<" + cls.size_fmt + string_fmt).pack_into_file(file, (size, *data))

        else:
            cls.exists_parser.pack_into_file(file, (0))


class NullParser(object):

    @classmethod
    def read_from(cls, file):
        pass

    @classmethod
    def write_to(cls, file, data):
        pass


class PadByteParser(object):
    parser = byte_parser

    @classmethod
    def read_from(cls, file):
        val, = cls.parser.unpack_from_file(file)

        if val != 0:
            print(val)

    @classmethod
    def write_to(cls, file):
        cls.parser.pack_into_file(file, (0))


class PadIntParser(object):
    parser = int_parser

    @classmethod
    def read_from(cls, file):
        val, = cls.parser.unpack_from_file(file)

        if val != 0:
            print(val)

    @classmethod
    def write_to(cls, file):
        cls.parser.pack_into_file(file, (0))


class PadLongParser(object):
    parser = long_parser

    @classmethod
    def read_from(cls, file):
        val, = cls.parser.unpack_from_file(file)

        if val != 0:
            print(val)

    @classmethod
    def write_to(cls, file):
        cls.parser.pack_into_file(file, (0))


class Fields:
    "All serialized objects have a collection of optional fields based on their type."

    # TODO: Figure out format/size of all used fields. 
    # TODO: Figure out actual meaning of fields.

    base_fields = (
        ("current_art", DefaultParser),
        ("position", PositionParser),
        ("offset_x", DefaultParser),
        ("offset_y", DefaultParser),
        ("shadow", DefaultParser),
        ("overlay_front", ArrayParser),
        ("overlay_back", ArrayParser),
        ("underlay", ArrayParser),
        ("blit_flags", DefaultParser),
        ("blit_color", DefaultParser),
        ("blit_alpha", DefaultParser),
        ("blit_scale", DefaultParser),  
        ("light_flags", DefaultParser),
        ("light_art", DefaultParser),
        ("light_color", DefaultParser),
        ("overlay_light_flags", ArrayParser),
        ("overlay_light_art", ArrayParser),
        ("overlay_light_color", ArrayParser),
        ("object_flags_1", DefaultParser),
        ("object_flags_2", DefaultParser),
        ("blocking_mask", DefaultParser),
        ("internal_name ", DefaultParser),
        ("known_name", DefaultParser),
        ("art", DefaultParser),
        ("destroyed_art", DefaultParser),
        ("armor_class", DefaultParser),
        ("hit_points", DefaultParser),
        ("hit_points_adj", DefaultParser),
        ("hit_points_damage", DefaultParser),
        ("material", DefaultParser),
        ("resistances", ArrayParser),
        ("scripts", ArrayParser),
        ("sound_bank", DefaultParser),
        ("category", DefaultParser),
        ("base_34", PadByteParser),
        ("base_35", PadByteParser),
        *(("base_%d" % i, NullParser) for i in range(36, 64))
    )

    item_fields = (
        ("item_flags", DefaultParser),
        ("item_parent", ArrayParser),
        ("item_weight", DefaultParser),
        ("item_weight_magic_adj", DefaultParser),
        ("item_worth", DefaultParser),
        ("item_mana_store", DefaultParser),
        ("item_inv_art", DefaultParser),
        ("item_inv_location", DefaultParser),
        ("item_use_art_fragment", DefaultParser),
        ("item_magic_tech_complexity", DefaultParser),
        ("item_discipline", DefaultParser),
        ("item_description_unknown", DefaultParser),
        ("item_description_effects", DefaultParser),
        ("item_spell_1", DefaultParser),
        ("item_spell_2", DefaultParser),
        ("item_spell_3", DefaultParser),
        ("item_spell_4", DefaultParser),
        ("item_spell_5", DefaultParser),
        ("item_spell_mana_store", DefaultParser),
        ("item_ai_action", DefaultParser),
        ("item_20", PadIntParser),
        ("item_21", PadByteParser),
        ("item_22", PadByteParser),
        *(("item_%d" % i, NullParser) for i in range(23, 32))
    )

    critter_fields = (
        ("critter_flags_1", DefaultParser),
        ("critter_flags_2", DefaultParser),
        ("critter_stats", ArrayParser),
        ("critter_skills", ArrayParser),
        ("critter_techs", ArrayParser),
        ("critter_spells", ArrayParser),
        ("critter_fatigue_points", DefaultParser),
        ("critter_fatigue_adj", DefaultParser),
        ("critter_fatigue_damage", DefaultParser),
        ("critter_crit_hit", DefaultParser),
        ("critter_effects", ArrayParser),
        ("critter_effects_cause", ArrayParser),
        ("critter_fleeing_from", ByteParser),
        ("critter_portrait", DefaultParser),
        ("critter_gold", ByteParser),
        ("critter_arrows", ByteParser),
        ("critter_bullets", ByteParser),
        ("critter_power_cells", ByteParser),
        ("critter_fuel", ByteParser),
        ("critter_inv_num", DefaultParser),
        ("critter_inv_list", ArrayParser),
        ("critter_inv_source", DefaultParser),
        ("critter_description_unknown", DefaultParser),
        ("critter_followers", ArrayParser),
        ("critter_teleport_destination", ByteParser),
        ("critter_teleport_map", DefaultParser),
        ("critter_death_time", DefaultParser),
        ("critter_auto_level_scheme", DefaultParser),
        ("critter_28", PadLongParser),
        ("critter_29", PadIntParser),
        ("critter_30", PadByteParser),
        ("critter_31", PadByteParser),
    )

    wall_fields = (
        *base_fields,
        ("wall_flags", DefaultParser),
        ("wall_1", PadIntParser),
        ("wall_2", PadByteParser),
        ("wall_3", PadByteParser),
        *(("wall_%d" % i, NullParser) for i in range(4, 32))
    )

    portal_fields = (
        *base_fields,
        ("portal_flags", DefaultParser),
        ("portal_lock_difficulty", DefaultParser),
        ("portal_key_id", DefaultParser),
        ("portal_notify_npc", DefaultParser),
        ("portal_4", PadIntParser),
        ("portal_5", PadIntParser),
        ("portal_6", PadByteParser),
        ("portal_7", PadByteParser),
        *(("portal_%d" % i, NullParser) for i in range(8, 32))
    )

    container_fields = (
        *base_fields,
        ("container_flags", DefaultParser),
        ("container_lock_difficulty", DefaultParser),
        ("container_key_id", DefaultParser),
        ("container_inventory_num", DefaultParser),
        ("container_inventory_list", ArrayParser),
        ("container_notify_npc", DefaultParser),
        ("container_6", PadIntParser),
        ("container_7", PadIntParser),
        ("container_8", PadByteParser),
        ("container_9", PadByteParser),
        *(("container_%d" % i, NullParser) for i in range(10, 32))
    )

    scenery_fields = (
        *base_fields,
        ("scenery_flags", DefaultParser),
        ("scenery_whois_in_me", ArrayParser),
        ("scenery_respawn_delay", DefaultParser),
        ("scenery_3", PadIntParser),
        ("scenery_4", PadByteParser),
        ("scenery_5", PadByteParser),
        *(("scenery_%d" % i, NullParser) for i in range(6, 32))
    )

    projectile_fields = (
        *base_fields,
        ("projectile_flags", DefaultParser),
        ("projectile_combat_damage", DefaultParser),
        ("projectile_hit_location", ArrayParser),
        ("projectile_parent_weapon", DefaultParser),
        ("projectile_4", PadIntParser),
        ("projectile_5", PadIntParser),
        ("projectile_6", PadByteParser),
        ("projectile_7", PadByteParser),
        *(("projectile_%d" % i, NullParser) for i in range(8, 32))
    )

    weapon_fields = (
        *base_fields,
        *item_fields,
        ("weapon_flags", DefaultParser),
        ("weapon_paper_doll_art", DefaultParser),
        ("weapon_hit", DefaultParser),
        ("weapon_hit_magic_adj", DefaultParser),
        ("weapon_damage_lower", ArrayParser),
        ("weapon_damage_upper", ArrayParser),
        ("weapon_damage_magic_adj", ArrayParser),
        ("waepon_speed", DefaultParser),
        ("weapon_speed_magic_adj", DefaultParser),
        ("weapon_range", DefaultParser),
        ("weapon_range_magic_adj", DefaultParser),
        ("weapon_min_strength", DefaultParser),
        ("weapon_min_strength_magic_adj", DefaultParser),
        ("weapon_ammo_type", DefaultParser),
        ("weapon_ammo_consumption", DefaultParser),
        ("weapon_missile_art", DefaultParser),
        ("weapon_visual_effect_art", DefaultParser),
        ("weapon_crit_hit", DefaultParser),
        ("weapon_crit_hit_magic_chance", DefaultParser),
        ("weapon_crit_hit_magic_effect", DefaultParser),
        ("weapon_crit_miss", DefaultParser),
        ("weapon_crit_miss_magic_chance", DefaultParser),
        ("weapon_crit_miss_magic_effect", DefaultParser),
        ("weapon_23", PadIntParser),
        ("weapon_24", PadIntParser),
        ("weapon_25", PadByteParser),
        ("weapon_26", PadByteParser),
        *(("weapon_%d" % i, NullParser) for i in range(27, 32))
    )

    ammo_fields = (
        *base_fields,
        *item_fields,
        ("ammo_flags", DefaultParser),
        ("ammo_quantity", DefaultParser),
        ("ammo_type", DefaultParser),
        ("ammo_3", PadIntParser),
        ("ammo_4", PadIntParser),
        ("ammo_5", PadByteParser),
        ("ammo_6", PadByteParser),
        *(("ammo_%d" % i, NullParser) for i in range(7, 32))
    )

    armor_fields = (
        *base_fields,
        *item_fields,
        ("armor_flags", DefaultParser),
        ("armor_paper_doll_art", DefaultParser),
        ("armor_ac_adj", DefaultParser),
        ("armor_ac_madj", DefaultParser),
        ("armor_resistances", ArrayParser),
        ("armor_resistances_madj", ArrayParser),
        ("armor_silent_move_adj", DefaultParser),
        ("armor_silent_move_madj", DefaultParser),
        ("armor_unarmed_damage", DefaultParser),
        ("armor_9", PadIntParser),
        ("armor_10", PadByteParser),
        ("armor_11", PadByteParser),
        *(("armor_%d" % i, NullParser) for i in range(12, 32))
    )


    gold_fields = (
        *base_fields,
        *item_fields,
        ("gold_flags", DefaultParser),
        ("gold_quantity", DefaultParser),
        ("gold_2", PadIntParser),
        ("gold_3", PadIntParser),
        ("gold_4", PadByteParser),
        ("gold_5", PadByteParser),
        *(("gold_%d" % i, NullParser) for i in range(6, 32))
    )

    food_fields = (
        *base_fields,
        *item_fields,
        ("food_flags", DefaultParser),
        ("food_1", PadIntParser),
        ("food_2", PadIntParser),
        ("food_3", PadByteParser),
        ("food_4", PadByteParser),
        *(("food_%d" % i, NullParser) for i in range(5, 32))
    )

    scroll_fields = (
        *base_fields,
        *item_fields,
        ("scroll_flags", DefaultParser),
        ("scroll_1", PadIntParser),
        ("scroll_2", PadIntParser),
        ("scroll_3", PadByteParser),
        ("scroll_4", PadByteParser),
        *(("scroll_%d" % i, NullParser) for i in range(5, 32))
    )

    key_fields = (
        *base_fields,
        *item_fields,
        ("key_id", DefaultParser),
        ("key_1", PadIntParser),
        ("key_2", PadIntParser),
        ("key_3", PadByteParser),
        ("key_4", PadByteParser),
        *(("key_%d" % i, NullParser) for i in range(5, 32))
    )

    key_ring_fields = (
        *base_fields,
        *item_fields,
        ("key_ring_flags", DefaultParser),
        ("key_ring_list", ArrayParser),
        ("key_ring_2", PadIntParser),
        ("key_ring_3", PadIntParser),
        ("key_ring_4", PadByteParser),
        ("key_ring_5", PadByteParser),
        *(("key_ring_%d" % i, NullParser) for i in range(6, 32))
    )

    written_fields = (
        *base_fields,
        *item_fields,
        ("written_flags", DefaultParser),
        ("written_type", DefaultParser),
        ("written_subtype", DefaultParser),
        ("written_text_end_line", DefaultParser),
        ("written_4", PadIntParser),
        ("written_5", PadIntParser),
        ("written_6", PadByteParser),
        ("written_7", PadByteParser),
        *(("written_%d" % i, NullParser) for i in range(8, 32))
    )

    generic_fields = (
        *base_fields,
        *item_fields,
        ("generic_flags", DefaultParser),
        ("generic_bonus", DefaultParser),
        ("generic_count", DefaultParser),
        ("generic_3", PadByteParser),
        ("generic_4", PadByteParser),
        *(("generic_%d" % i, NullParser) for i in range(5, 32))
    )

    player_fields = (
        *base_fields,
        *critter_fields,
        ("player_flags", DefaultParser),
        ("player_flags_fate", DefaultParser),
        ("player_reputations", ArrayParser),
        ("player_reputations_ts", ArrayParser),
        ("player_background", DefaultParser),
        ("player_background_text", DefaultParser),
        ("player_quests", ArrayParser),
        ("player_blessings", ArrayParser),
        ("player_blessings_ts", ArrayParser),
        ("player_curses", ArrayParser),
        ("player_curses_ts", ArrayParser),
        ("player_party_id", DefaultParser),
        ("player_rumors", ArrayParser),
        ("player_13", ArrayParser),
        ("player_schematics", ArrayParser),
        ("player_logbook_ego", ArrayParser),
        ("player_fog_mask", DefaultParser),
        ("player_name", StringParser),
        ("player_bank_money", DefaultParser),
        ("player_global_flags", ArrayParser),
        ("player_global_vars", ArrayParser),
        ("player_21", PadIntParser),
        ("player_22", PadIntParser),
        ("player_23", PadByteParser),
        ("player_24", PadByteParser),
        *(("player_%d" % i, NullParser) for i in range(25, 64))
    )

    npc_fields = (
        *base_fields,
        *critter_fields,
        ("npc_flags", DefaultParser),
        ("npc_leader", ByteParser),
        ("npc_ai_packet", DefaultParser),
        ("npc_combat_focus", ByteParser),
        ("npc_who_hit_me_last", ByteParser),
        ("npc_experience_worth", DefaultParser),
        ("npc_experience_pool", DefaultParser),
        ("npc_waypoints", ArrayParser),
        ("npc_current_waypoint", DefaultParser),
        ("npc_standpoint_day", ArrayParser),
        ("npc_standpoint_night", ArrayParser),
        ("npc_origin", DefaultParser),
        ("npc_faction", DefaultParser),
        ("npc_retail_price_multiplier", DefaultParser),
        ("npc_substitute_inventory", ArrayParser),
        ("npc_reaction_base", DefaultParser),
        ("npc_social_class", DefaultParser),
        ("npc_reaction_pc", ArrayParser),
        ("npc_reaction_level", ArrayParser),
        ("npc_reaction_time", ArrayParser),
        ("npc_wait", DefaultParser),
        ("npc_generator", DefaultParser),
        ("npc_22", PadIntParser),
        ("npc_damages", ArrayParser),
        ("npc_shitlist", ArrayParser),
        *(("npc_%d" % i, NullParser) for i in range(25, 64))
    )

    trap_fields = (
        *base_fields,
        ("trap_flags", DefaultParser),
        ("trap_difficulty", DefaultParser),
        ("trap_2", PadIntParser),
        ("trap_3", PadByteParser),
        ("trap_4", PadByteParser),
        *(("trap_%d" % i, NullParser) for i in range(5, 32))
    )