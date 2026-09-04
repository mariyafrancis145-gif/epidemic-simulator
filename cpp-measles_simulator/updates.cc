#include <algorithm>
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <unordered_map>

#include "updates.h"
#include "interventions.h"
#include "testing.h"

using std::cerr;
using std::vector;

// -----------------------------------------------------------------------------
// OUTGOING FORCE OF INFECTION
// These functions calculate how much infection an infectious agent contributes
// in each location.
// -----------------------------------------------------------------------------

double update_individual_lambda_h(const agent& node, int cur_time)
{
    (void)cur_time;

    return (node.infective ? 1.0 : 0.0)
        * node.kappa_T
        * node.infectiousness
        * node.kappa_H;
}


double update_individual_lambda_w(const agent& node, int cur_time)
{
    (void)cur_time;

    return (node.infective ? 1.0 : 0.0)
        * (node.attending ? 1.0 : GLOBAL.ATTENDANCE_LEAKAGE)
        * node.kappa_T
        * node.infectiousness
        * node.kappa_W;
}


double update_individual_lambda_c(const agent& node, int cur_time)
{
    (void)cur_time;

    return (node.infective ? 1.0 : 0.0)
        * node.kappa_T
        * node.infectiousness
        * node.funct_d_ck
        * node.kappa_C
        * node.zeta_a;
}
    
double update_individual_lambda_nbr_cell(
    const agent& node,
    int cur_time)
{
    (void)cur_time;

    return (node.infective ? 1.0 : 0.0)
        * node.kappa_T
        * node.infectiousness
        * node.kappa_C
        * node.zeta_a;
}


double update_individual_lambda_travel(
    const agent& node,
    int cur_time)
{
    (void)cur_time;

    // Base travel contribution.
    // More detailed transport type, journey duration and passenger mixing
    // can be introduced later.
    if (!node.travels)
    {
        return 0.0;
    }

    return (node.infective ? 1.0 : 0.0)
        * node.kappa_T
        * node.infectiousness
        * node.kappa_travel;
}


