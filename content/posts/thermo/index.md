+++
title = "Basics of thermodynamics"
date = 2026-11-21
description = "A physicist's ramblings to address some of the oft-skipped-over details about thermodynamics from a potential-first point of view"

[extra]
math = true
+++
Thermodynamics is the study of macroscopic systems and how they respond to
heat applied or work done to/by the system.

There are two laws we will be interested in:

First law: Change in internal energy in a system will be the difference of the
heat flow **into** the system and the work done **by** the system
```math
\Delta U = Q - W,
```
where the **into** and **by** define the sign convention.

Second law: For a process in an isolated system, the change in entropy will
always be positive or zero
```math
\Delta S \ge 0,
```
and is only zero for a reversible process.

However, in practice we rarely deal with isolated systems, and instead work
with systems that are in contact with large reservoirs that can exchange some
quantity such as energy, volume, etc. In practice that means that we will often
work with quantities besides internal energy `$U$` or entropy `$S$` and instead use 
concepts such as Helmholtz free energy `$\mathcal{F}$` or enthalpy `$\mathcal{H}$`. 
These other quantities are known as thermodynamic potentials, and these notes 
attempt to lay out the common thermodynamic potentials, such as the Helmholtz 
free energy or enthalpy, and explain them NOT in the traditional way I've seen 
used, but instead simply as the natural mathematical expression for systems 
that are in contact with larger systems where we allow one or more of the 
explicit independent variables to be exchanged with a reservoir.

Traditional explanation:
> Helmholtz free energy: A measure of useful work obtainable from a system at
> constant temperature and volume.

Potential explanation:
> Helmholtz free energy: thermodynamic potential for a system that is in contact
> with a system that can exchange energy such that temperature is fixed.

## Relation to Stat-Mech

We know that thermodynamics comes from statistical mechanics, where the 
macroscopic system is treated as a collection of a very large number of 
microscopic constituents such as particles or magnetic dipoles in a lattice.
Physically, we say that the full system is constantly changing in the
complete specification of constituents, which is also known as a microstate. 
Large collections of microstates will have equivalent thermodynamic
variables such as total energy `$U$` or total volume `$V$`, and that collection of
microstates is known as a macrostate, and the count of microstates is given
by the expression
```math
\sum_{s \in \mu\text{-states}} 1 = \Omega(U,V,N,\ldots),
```
which is called the microcanonical ensemble.

The second law then becomes a statistical statement that if each microstate is 
equally likely for an isolated system then the system will most likely be in 
the macrostate (set of thermodynamic variables) that has the **most** 
microstates in it, i.e. `$\Omega$` is maximal, and we get the Boltzmann 
definition of entropy
```math
S(U,V,N,\ldots) = k_B \ln \Omega(U,V,N,\ldots).
```

There are other ensembles that can be written using similar notation
```math
\sum_{s \in \mu\text{-states}} W(s) = \mathcal{Z},
```
where `$s$` indexes the microstates, `$W(s)$` is a weight of a given microstate 
with the given internal variables, and `$\mathcal{Z}$` is known as a partition 
function. For a system in contact with a reservoir at constant temperature, 
we work with the canonical ensemble and get the following expression for the 
canonical partition function
```math
\sum_{s \in \mu\text{-states}} e^{-E(s)/k_B T} = Z,
```
where `$E(s)$` is the energy for a given microstate, and using a similar 
formula we get the Massieu potential
```math
\Phi = k_B \ln Z.
```
We will NOT cover the details of this relationship in these notes, but this 
DOES give us the motivation for wanting to extremize some function `$\Psi$` with
respect to the unconstrained variables (ex: energy split between subsystems), 
which we'll identify as a thermodynamic potential, to find the equilibrium 
state of a system when in contact with a reservoir that can exchange some 
quantity (energy/heat, volume, particles, etc.).

## Thermodynamic potentials

A general thermodynamic potential `$\Psi$` has 3 roles:

* Acts as the selector: Extremizing, finding the stationary point
`$\mathrm{d} \Psi = 0$` with respect to unconstrained variables, yields the state
of the system at equilibrium when in contact with some external reservoir.
* Generator: Partial derivatives of the potential yield the equations of
state of the system when in contact with external reservoir.
* Helps with energy accounting: The change in the potential `$\Delta \Psi$`
is related (equality or directed inequality) to the exchanged quantity when 
in contact with some reservoir.

I will here give a list of the thermodynamic potentials, and they break into
two sets: entropy-like or energy-like.

Entropy-like potentials:

| Potential Name | Symbol | Natural Variables |
|----------------|--------|-------------------|
| Entropy        | `$S$`    | `$(U,V,N,\ldots)$`    |
| Massieu Potential | `$\Phi$` | `$(\tfrac{1}{T},V,N,\ldots)$` |
| Planck Potential | `$\Xi$` | `$(\tfrac{1}{T},\tfrac{P}{T},N,\ldots)$` |

Energy-like potentials:

| Potential Name | Symbol | Natural Variables |
|----------------|--------|-------------------|
| Internal Energy | `$U$` | `$(S,V,N,\ldots)$` |
| Helmholtz Free Energy | `$\mathcal{F}$` | `$(T,V,N,\ldots)$` |
| Gibbs Free Energy | `$\mathcal{G}$` | `$(T,P,N,\ldots)$` |
| Grand Potential | `$\Phi_G$` | `$(T,V,\mu,\ldots)$` |
| Enthalpy | `$\mathcal{H}$` | `$(S,P,N,\ldots)$` |

It should be noted that the entropy-like potentials are often used in Stat-Mech
because they directly relate to the partition functions you can create from the
microscopic systems using a similar definition as the Boltzmann entropy
```math
\Psi = k_B \ln \mathcal{Z}.
```
On the other hand, the energy-like potentials are often used in traditional 
thermodynamics problems, largely because the natural variables are those that 
are directly measurable/under control.

A few distinct points to note:
* `$S(U,V,\ldots) \leftrightarrow U(S,V,\ldots)$` are mathematical inverses of
each other describing the same system but from two different points of view.
* The two energy-like potentials internal energy `$U(S,V,\ldots)$` and 
`$\mathcal{H}(S,P,\ldots)$` both have entropy as an independent variable, and 
these potentials are often used either to model energy transferred in constant 
volume or constant pressure systems or to model isentropic processes where 
`$\mathrm{d} S = 0$`.
* The pairs `$\Phi \leftrightarrow \mathcal{F}$`, and
`$\Xi \leftrightarrow \mathcal{G}$`, are the same quantity up to a multiplicative 
factor `$-\tfrac{1}{T}$` since the reservoir fixes `$T$`, and the minus sign is why
the entropy-like potentials are maximized and energy-like potentials are 
minimized.
* The grand potential `$\Phi_G$` (which is a separate unrelated potential from
the Massieu potential `$\Phi$`) is ALSO equivalent to an entropy-like quantity
`$S - U/T + \mu N/T$` that is equivalent up to the same multiplicative 
factor `$-\tfrac{1}{T}$`, but it is rarely used in entropy form. It is listed here 
because it is one of the more common connections to stat-mech, through
the partition function of the so-called "grand canonical ensemble".
* The enthalpy `$\mathcal{H}$` does NOT have an entropy equivalent as a
Legendre transform from the entropy similar to the Massieu and Planck 
potentials. The natural pair (which would be `$S - PV/T$`, see the Legendre
transform section below) has natural variables of `$(U, P/T, \ldots)$` and the 
reservoir would exchange volume at fixed `$P/T$` while leaving `$U$` fixed. This is
a very awkward reservoir, because it would be exchanging volume at a
given pressure `$P$`, doing work, without exchanging energy: a nearly 
contradictory condition.

## Isolated system: Entropy as potential

Consider an isolated system that cannot exchange anything with its 
environment, no energy, no volume, no particles, nothing. From the above
motivation, we want to represent this through an expression that is
'stationary' with respect to fluctuations. In mathematical terms we would
write that as a function 
```math
S(U,V,N_a,\ldots) 
```
where energy `$U$`, volume `$V$`, number of particles `$N_a$`, are the explicit 
independent variables defining the system. One thing to note: all the 
independent variables are so-called 'extensive' variables, and they depend 
on the size of the system. Explicitly, that means that if you combine two 
systems, then you add the values of the extensive variables.

Using this function, we can talk about the first job of a thermodynamic 
potential: it acts as a **selector** and ranks the states such that 
extremizing (maximizing for entropy-like potentials, minimizing for energy-like
potentials) over the internal unconstrained variables, such as
how energy is split between subsystems (see section below), identifies the
equilibrium condition.

### Definition of temperature

Let's now identify this potential with a name **Entropy**. Recall that the
thermodynamic definition of entropy (i.e. Clausius' definition vs the
stat-mech or Boltzmann definition) is
```math
\mathrm{d} S = \frac{1}{T} \delta Q_{\text{rev}},
```
where `$\delta Q_{\text{rev}}$` is the heat flow for a reversible process. We 
can compare that to a differential of our potential
```math
\mathrm{d}S =
\frac{\partial S}{\partial U} \mathrm{d} U +
\frac{\partial S}{\partial V} \mathrm{d} V + 
\frac{\partial S}{\partial N_a} \mathrm{d} N_a + \ldots.
```
If we say that other quantities (`$V$`, `$N_a$`, etc.) are fixed and we identify
the change in energy as the heat `$\mathrm{d} U = \delta Q$`, then the partial
derivative of the entropy with respect to internal energy is the inverse 
temperature
```math
\frac{\partial S}{\partial U} = \frac{1}{T}.
```

This highlights the second property of a thermodynamic potential, as a 
**generator**, whose partial derivatives define the so-called "equations of
state".

### Systems in thermal equilibrium

Why do this? Let's consider what happens when we separate the system into two
pieces, system 1 and system 2 such that the total entropy is `$S = S_1 + S_2$`. 
In equilibrium that total entropy will be stationary, i.e. 
`$\mathrm{d} S_1 + \mathrm{d} S_2 = 0$`, so we can write the sum as
```math
0 = 
\left(
  \frac{\partial S_1}{\partial U_1} \mathrm{d} U_1 +
  \frac{\partial S_2}{\partial U_2} \mathrm{d} U_2
\right) + 
\ldots.
```
Since the system is isolated, we know the total energy is fixed. So if the wall
between the two subsystems allows **only** energy to flow, we know that 
`$\mathrm{d} U_1 = -\mathrm{d} U_2$`, and identifying the partial derivative with 
the inverse temperatures we get that, for systems in equilibrium, 
`$T_1 = T_2$`. It should be noted that there is an even stronger statement: 
since `$\Delta S \ge 0$`, when out of equilibrium energy must flow from the 
system with higher temperature to that with lower temperature. However, for 
these notes I want to focus on the fact that partial derivatives for systems in
equilibrium must match because that motivates using Legendre transforms below 
for looking at systems in contact with external reservoirs.

### System in contact with large reservoir

Let's consider the small system in contact with a much larger system such
that the total entropy is
```math
S_{\text{tot}}(U_{\text{tot}}) = 
S_{\text{sys}}(U) + S_{\text{res}}(U_{\text{tot}} - U),
```
where we assume that the total energy is much larger than the energy in
the small system `$U \ll U_{\text{tot}}$`. We can expand the entropy of the 
reservoir
```math
S_{\text{res}}(U_{\text{tot}} - U) \approx
S_{\text{res}}(U_{\text{tot}}) -
\left.\frac{\partial S_{\text{res}}}{\partial U_{\text{res}}}
\right|_{U_{\text{res}}=U_{\text{tot}}} \, U,
```
where the first term is a constant that doesn't depend on the amount of energy
in the system `$U$`.

There are two consequences of this:
* The internal energy `$U$` in the system will be determined by the equivalence 
of the partial derivatives between the system and the much larger reservoir.
Since the change in energy is negligible compared to the reservoir's total energy, the
partial derivative (and hence temperature) is fixed.
* Maximizing the entropy of the system plus reservoir is equivalent to maximizing
the combined expression
```math
S_{\text{sys}} -
\left(\frac{\partial S_{\text{res}}}{\partial U_{\text{res}}}\right)
U.
```

## Internal Energy

As an alternative formulation, we can invert the entropy function to have the 
total internal energy `$U$` as the dependent variable with entropy as an
independent variable
```math
U(S,V,\ldots).
```
In this case, the internal energy `$U$` still acts as a thermodynamic potential
in the same senses as in the entropy section:

* **selector** Here, the selector acts to select the system with minimum energy
at a fixed entropy. I don't have a good explanation for this, but we can show
it through a proof by contradiction. Consider a system that is at a max entropy 
`$S$` for a given `$U$`, but not at minimum `$U$` for that `$S$`. We could then extract
work `$W$` in a reversible manner at a fixed entropy `$S$` lowering the internal 
energy `$U$`, and then return that energy as heat, increasing the entropy. This 
contradicts our starting assumption that `$S$` was maximum for that `$U$`.
* **generator** Using the inverse function theorem we get
```math
\frac{\partial U}{\partial S} = T,
```
and using the classical physics definition of work and force we get
```math
\frac{\partial U}{\partial V} = -P,
```
where partial derivatives hold all other natural variables fixed. We see that
the derivatives of energy with respect to the natural variables give well 
understood measurable properties that are also often controllable in 
experimental setups.

Note: This definition of pressure also gives us the full definition of the
partial derivative of entropy with respect to volume using the triple product 
rule
```math
\frac{\partial S}{\partial V} = \frac{P}{T}.
```

There is another reason to use the internal energy, to help with **energy 
accounting** when using the first law. For example, we define the heat capacity
at constant volume
```math
C_V = \left(\frac{\partial U}{\partial T}\right)_V,
```
to help describe how energy in a system changes with temperature at fixed 
volume. We can also identify the change in energy for a constant volume system
for an isentropic (no change in entropy) process as the work done by other 
(non-expansion) reversible sources **ON** the system, for example electric or 
magnetic systems
```math
\Delta U = W_{\text{other},\text{rev}}.
```

## Legendre Transform

The Legendre transform is a mathematical tool used to transform a function of an
independent variable into a different function of the derivative of the 
independent variable without any loss of information. This expression turns out
to be very useful for minimum problems, where you need to fix one or more 
derivatives. This is exactly what we want to do if we want to model a 
thermodynamic system in contact with a reservoir that fixes one of the partial
derivatives, for example fixed temperature or pressure.

Consider a function `$f(x)$` that is strictly convex on an interval `$[a,b]$`, 
which can be modeled as a set of points `$(x, f(x))$`. Since the function is 
convex, the same function can be represented by the set of tangent lines that 
just touch the function. The tangent lines are also specified by a pair of 
numbers, the slope `$p = f'(x)$` and intercept, giving the pair `$(p, g(p))$` where
the `$g(p)$` will capture the intercept.

Mechanically, to use this, we need to invert the derivative 
`$f'(x) = p(x) \to x(p)$` (and the strict convexity of `$f(x)$` is what guarantees
the inverse exists) and then we can solve for the intercept and find
```math
g(p) = f(x(p)) - x(p) p,
```
and notice that this structure is the same (up to a sign) as the expression we
found above that we would maximize for a system in thermal contact with a 
reservoir. This gives the new expression the first role as a thermodynamic 
potential as a **selector**. Taking the derivative of this expression gives
```math
g'(p) = f'(x(p))\, x'(p) - x'(p) p - x(p),
```
but we already defined `$f'(x) \equiv p$` so the first two terms cancel, yielding
```math
g'(p) = -x(p),
```
the inverse of the original definition, and gives the **generator** property
for the transformed function.

## Free energy and Free entropy

One of the most common systems we look at will be systems in thermal contact
with a reservoir such that the temperature of the system is fixed. We've
already seen why maximizing entropy of the system + reservoir is the same
as simply maximizing this new quantity that only depends on system quantities
```math
\Phi = S - \frac{U}{T},
```
that is called the Massieu potential or Helmholtz free entropy. Even though
the potential is written as the deceptively simple `$S-U/T$`, the implicit `$U$` 
in the entropy `$S$` as well as the explicit `$U$` in the formula are replaced by
inverting the partial derivative definition of inverse temperature as laid
out in the Legendre transform section.

If we instead work with the system + reservoir from an internal energy point of
view we would find that we need to minimize the new expression
```math
\mathcal{F} = U - T S,
```
where again we would replace the implicit `$S$` in the internal energy and the
explicit `$S$` in the formula by inverting the partial derivative. However
we can compare the two simple formulas to identify that the two expressions
are equivalent up to a multiplicative factor
```math
\Phi \equiv - \frac{\mathcal{F}}{T}.
```

The term "Free energy" comes from the concept of work that is available or free
to be extracted from the system given the constraint of constant temperature.
This again covers the third **energy accounting** role of a thermodynamic 
potential, and for the Helmholtz free energy can be captured by the equation
```math
W_{\text{by}} \le -\Delta \mathcal{F},
```
and this becomes the source of the 'traditional' definition of the potential.
Note: the term "Free entropy" is recognition that the two potentials are 
equivalent up to the multiplicative factor for systems in thermal contact with
a reservoir such that they have a fixed temperature.

In addition to the Helmholtz free energy we can also fix other quantities, such as 
pressure, to get the Gibbs free energy
```math
\mathcal{G} = \mathcal{F} + P V,
```
or chemical potential to get the grand potential
```math
\Phi_G = \mathcal{F} - \mu N,
```
and we can transform these to the entropy form by negating the sign and scaling
by the fixed inverse temperature of the system.

## Enthalpy

The enthalpy is an energy-like thermodynamic potential that plays a slightly 
different role compared to the free energies because it does NOT fix 
temperature, instead leaving entropy as an independent variable. As such, the 
enthalpy is rarely used as a **selector**. 

However, enthalpy still actively plays a role as a generator in compressible
fluid systems. For example, the first derivative of enthalpy with respect to
pressure (at constant entropy) is the volume, and the derivative of the 
volume with respect to pressure will define how pressure waves move, so it
defines the speed of sound
```math
\left(\frac{\partial^2 \mathcal{H}}{\partial P^2}\right)_S = 
\left(\frac{\partial V}{\partial P}\right)_S = -\frac{V}{\rho a^2},
```
where `$\rho$` is the density and `$a$` the speed of sound. In particular, the 
systems where we use the enthalpy derived equations of state are those where
the flow or change is fast compared to the time it takes for heat to flow and
where there is low friction/no shock waves such that the process is reversible.
In such cases we expect entropy to be fixed (`$\mathrm{d} S = 0$`), and in
steady-flow systems the first law combines internal energy `$U$` and flow work 
`$PV$`, so we can define the specific enthalpy
```math
h = u + P/\rho,
```
where `$u$` is the internal energy per unit mass (specific internal energy)
and `$\rho$` is the fluid density. Using the specific enthalpy along with
the specific kinetic energy and specific gravitational potential energy
```math
h + \tfrac{v^2}{2} + g z,
```
we can identify the energy carried through a steady flow.

In addition, enthalpy is very commonly used in **energy accounting** for
systems not at fixed volume, but instead exposed to a fixed atmospheric
pressure. In these systems at constant pressure we can define the work done
from the change in volume `$W_{\text{by}} = P \Delta V$` and using the first
law we can identify
```math
\Delta U + P \Delta V = Q,
```
where we can identify the left-hand side as the change in enthalpy. So the
heat added to a system at constant pressure for changes in state (latent heat 
of fusion or latent heat of vaporization) or chemical reactions (the heat of 
formation or heat of combustion) is quantified as the change of enthalpy of 
the system through the reaction. Similarly, the heat capacity at constant
pressure is defined in terms of the enthalpy
```math
C_P = \left(\frac{\partial \mathcal{H}}{\partial T}\right)_P.
```
Given these, enthalpy plays a very large role in energy accounting for 
physically realizable systems undergoing a phase change or chemical reaction.

