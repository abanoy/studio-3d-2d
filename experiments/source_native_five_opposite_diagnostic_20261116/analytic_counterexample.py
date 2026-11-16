"""Independent scalar equilibrium counterexample; no app/candidate/native reads.

Coordinates are synthetic, computed in memory, and never serialized. Output is
angles, scalar projections, constraint/step residuals and dot products only.
"""
import json
import math
from pathlib import Path


def main():
    # Same active50-stiffness coefficient group and Source unit factor as the
    # measured pair, with a synthetic authored folded two-link hierarchy.
    length=20.0*0.01905
    gravity=20.0*0.01905
    stiffness=50.0
    theta=math.radians(40.0)
    dt=1.0/120.0
    offset_ratio=1.2
    force=stiffness*length*math.sin(theta)+gravity*math.tan(theta)
    def child_tangent(beta):
        return (-stiffness*length*math.sin(beta)*math.cos(beta)
                +force*math.cos(theta+beta)-gravity*math.sin(theta+beta))
    low,high=0.0,math.pi/4
    assert child_tangent(low)>0 and child_tangent(high)<0
    # Derivative is negative throughout[0,pi/4]: all cos2b/sin(theta+b)/
    # cos(theta+b) terms are nonnegative, with positive force/gravity terms.
    for _ in range(180):
        middle=(low+high)/2
        if child_tangent(middle)>0:low=middle
        else:high=middle
    beta=(low+high)/2
    phi=theta+beta
    plus_lateral=length*(math.sin(phi)-offset_ratio*math.sin(theta))
    common_forward=length*(math.cos(phi)-offset_ratio*math.cos(theta)+offset_ratio-1)
    minus_lateral=-plus_lateral
    whole_dot=common_forward*common_forward+plus_lateral*minus_lateral
    # Independently perform one ordinary semi-implicit Euler+fixed-length
    # projection from each analytic equilibrium. No solver is imported.
    def projected_step(angle,goal_angle):
        spring=-stiffness*length*math.sin(angle-goal_angle)
        ax=force+spring*math.cos(goal_angle)
        az=gravity-spring*math.sin(goal_angle)
        before_x=length*math.sin(angle);before_z=length*math.cos(angle)
        vx=dt*ax;vz=dt*az
        px=before_x+dt*vx;pz=before_z+dt*vz
        norm=math.hypot(px,pz);ux=px/norm;uz=pz/norm
        tangent=vx*ux+vz*uz
        after_vx=vx-tangent*ux;after_vz=vz-tangent*uz
        return max(abs(length*ux-before_x),abs(length*uz-before_z),abs(after_vx),abs(after_vz))
    parent_tangent=(-stiffness*length*math.sin(theta)+force)*math.cos(theta)-gravity*math.sin(theta)
    child_residual=child_tangent(beta)
    step_error=max(projected_step(theta,0),projected_step(phi,theta))
    leaf_lateral=length*math.sin(theta)
    leaf_forward=length*(math.cos(theta)-1)
    leaf_dot=leaf_forward*leaf_forward-leaf_lateral*leaf_lateral
    assert 0<theta<math.pi/4 and 0<beta<math.pi/4
    assert plus_lateral>0 and minus_lateral<0 and whole_dot>0 and leaf_dot<0
    assert max(abs(parent_tangent),abs(child_residual),step_error)<1e-12
    result={'format':'has_opposite_world_dot_independent_counterexample_1','passed':True,
            'scope':'Synthetic admissible0x31 equilibrium; not actual Junko geometry, SDK/client execution or explanation of the unprobed failing native id.',
            'parent_relative_degrees':math.degrees(theta),'child_relative_degrees':math.degrees(beta),
            'world_child_degrees':math.degrees(phi),'cone_limit_degrees':45.0,
            'length_world_units':length,'stiffness':stiffness,'gravity_magnitude':gravity,
            'damping':5.0,'authored_backward_offset_in_link_lengths':offset_ratio,
            'exact_opposite_world_force_magnitude':force,
            'plus_force_axis_tip_displacement':plus_lateral,
            'minus_force_axis_tip_displacement':minus_lateral,
            'common_goal_axis_tip_displacement':common_forward,
            'whole_world_displacement_dot':whole_dot,
            'single_leaf_original_dot':leaf_dot,
            'parent_tangent_equilibrium_residual':parent_tangent,'child_tangent_equilibrium_residual':child_residual,
            'one_Euler_length_projection_residual_max':step_error,
            'native_arrays_or_tip_coordinates_serialized':False,'candidate_solver_imported':False,
            'engine_or_CIM_Git_network_used':False}
    path=Path(__file__).with_name('ANALYTIC_COUNTEREXAMPLE.json')
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
