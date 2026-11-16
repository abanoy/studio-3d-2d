"""Synthetic dimensional examples for a plan, not a model/runtime prototype."""
from fractions import Fraction as Q
from decimal import Decimal, localcontext
from pathlib import Path
import hashlib
import json
import struct

HERE=Path(__file__).resolve().parent
TARGET=6*Q(3048,10000)
SOURCE=Q(1905,100000)


def decimal(value):
    with localcontext() as context:
        context.prec=50
        return format(Decimal(value.numerator)/Decimal(value.denominator),'f')


def main():
    checks=[]
    def require(name,condition):
        assert condition,name
        checks.append(name)
    require('six_feet_exact_18288_over_10000_metres',TARGET==Q(18288,10000))
    require('source_unit_exact_381_over_20000',SOURCE==Q(381,20000))
    native_height=Q(100);native_length=Q(20)
    source_scale_before=SOURCE
    converted_height=native_height*SOURCE
    factor=TARGET/converted_height
    require('example_source_height_100_converts_to_1_905_metres',converted_height==Q(1905,1000))
    require('basis_factor_is_0_96_without_user_scale_change',factor==Q(96,100))
    require('user_scale_one_reaches_target',converted_height*factor==TARGET)
    require('user_scale_half_remains_artist_multiplier',converted_height*factor/2==Q(9144,10000))
    require('user_scale_two_remains_artist_multiplier',converted_height*factor*2==Q(36576,10000))
    require('source_conversion_is_not_rewritten',SOURCE==source_scale_before)
    normalized_length=native_length*SOURCE*factor
    require('native_rule_length_converts_once_through_actual_basis',normalized_length==Q(36576,100000))
    require('rewriting_source_scale_and_world_basis_would_double_apply_factor',native_length*(SOURCE*factor)*factor!=normalized_length)
    other_source=Q(1,100)
    other_factor=TARGET/(native_height*other_source)
    require('different_input_unit_produces_same_reference_height',native_height*other_source*other_factor==TARGET)
    require('native_length_is_covariant_under_alternative_source_unit',native_length*other_source*other_factor==normalized_length)
    for raw_root_scale in (Q(1,2),Q(2),Q(3,2)):
        local_height=native_height*SOURCE*raw_root_scale
        intrinsic=TARGET/local_height
        require('raw_root_scale_'+str(raw_root_scale)+'_is_counted_in_measurement_once',local_height*intrinsic==TARGET)
        require('raw_root_scale_'+str(raw_root_scale)+'_is_counted_in_rule_world_scale_once',native_length*SOURCE*raw_root_scale*intrinsic==normalized_length)
    parent_scale=Q(2)
    require('parent_group_artist_scale_is_preserved',converted_height*factor*parent_scale==TARGET*parent_scale)
    legacy_height=Q(16,10);legacy_user_scale=Q(2)
    require('legacy_absent_basis_keeps_existing_three_point_two_height',legacy_height*legacy_user_scale==Q(32,10))
    old_fitted_user_scale=factor
    require('old_optional_fit_metadata_stays_inert',converted_height*old_fitted_user_scale==TARGET)
    require('reinterpreting_old_fit_metadata_as_active_basis_changes_appearance',converted_height*old_fitted_user_scale*factor!=TARGET)
    quantized_factor=struct.unpack('<f',struct.pack('<f',float(factor)))[0]
    scalar_height=float(converted_height)*quantized_factor
    scalar_error=abs(scalar_height-float(TARGET))
    require('example_scalar_float32_factor_respects_existing_2e_5_gate',scalar_error<2e-5)
    result={
        'format':'six_foot_basis_synthetic_dimensions_1',
        'scope':'Exact rational dimensional examples plus one scalar float32 packing example; NOT importer/Godot/SDK/model qualification.',
        'checks':len(checks),'failures':0,'names':checks,
        'synthetic_example':{'native_height':'100','source_scale':decimal(SOURCE),'converted_height':decimal(converted_height),'factor':decimal(factor),'user_scale':'1','target_metres':decimal(TARGET),'native_rule_length':'20','normalized_rule_length_metres':decimal(normalized_length)},
        'scalar_float32_factor_height_error':scalar_error,
        'actual_engine_or_native_data_used':False,
    }
    (HERE/'DIMENSIONAL_EXAMPLES.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='names'},indent=2))


if __name__=='__main__':main()
