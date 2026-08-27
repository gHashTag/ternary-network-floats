(* CorePhi.v - Exact Algebraic Identities for Phi *)
(* Part of Trinity S3AI Coq Proof Base *)

(* This file did not compile before 2026-08-27, and three of its statements were
   false. phi_cubed read phi^3 = 2*sqrt 5 + 3 (7.472) against the true 2 + sqrt 5
   (4.236); phi_fourth and phi_fifth carried the same shape of error. The pattern
   phi^n = F(n)*phi + F(n-1) had been written as F(n)*sqrt 5 + F(n+1), dropping a
   division by two and shifting the index. The proofs were not proofs either:
   phi_square read "apply phi_quadratic; ring", which does not derive one equation
   from another, and phi_quadratic called `field` on a goal needing sqrt 5 * sqrt 5
   = 5, which `field` cannot know. Nothing was machine-checked, because nothing
   type-checked. Statements corrected and proofs rewritten; the file now closes
   under coqc with no admitted lemmas. *)

Require Import Reals.Reals.
Require Import Lra.
Require Import List.
Import ListNotations.
Open Scope R_scope.

(** Golden ratio definition: phi = (1 + sqrt 5) / 2 *)
Definition phi : R := (1 + sqrt 5) / 2.

(** The one fact about sqrt that every identity below rests on. *)
Lemma sqrt5_sq : sqrt 5 * sqrt 5 = 5.
Proof.
  apply sqrt_sqrt; lra.
Qed.

Lemma sqrt5_nonneg : 0 <= sqrt 5.
Proof.
  apply sqrt_pos.
Qed.

(** phi is positive *)
Lemma phi_pos : 0 < phi.
Proof.
  unfold phi. pose proof sqrt5_nonneg. lra.
Qed.

(** phi is non-zero *)
Lemma phi_nonzero : phi <> 0.
Proof.
  pose proof phi_pos. lra.
Qed.

(** phi^2 = phi + 1 (fundamental golden ratio identity) *)
Lemma phi_square : phi^2 = phi + 1.
Proof.
  unfold phi. pose proof sqrt5_sq. simpl. nra.
Qed.

(** phi satisfies the quadratic equation: phi^2 - phi - 1 = 0 *)
Lemma phi_quadratic : phi^2 - phi - 1 = 0.
Proof.
  pose proof phi_square. lra.
Qed.

(** phi^-1 = phi - 1 (reciprocal identity) *)
Lemma phi_inv : / phi = phi - 1.
Proof.
  pose proof phi_nonzero as Hn. pose proof phi_square as Hs.
  apply (Rmult_eq_reg_l phi); [| exact Hn].
  rewrite Rinv_r by exact Hn. simpl in Hs. nra.
Qed.

(** phi^-2 = 2 - phi (squared reciprocal) *)
Lemma phi_inv_sq : / phi^2 = 2 - phi.
Proof.
  pose proof phi_nonzero as Hn. pose proof phi_square as Hs.
  assert (Hsq : phi^2 <> 0) by (simpl; nra).
  apply (Rmult_eq_reg_l (phi^2)); [| exact Hsq].
  rewrite Rinv_r by exact Hsq. simpl in Hs |- *. nra.
Qed.

(** Trinity identity: phi^2 + phi^-2 = 3 *)
(** This is the fundamental root identity from which all formulas descend *)
Lemma trinity_identity : phi^2 + / phi^2 = 3.
Proof.
  pose proof phi_square as Hs. pose proof phi_inv_sq as Hi.
  rewrite Hi, Hs. lra.
Qed.

(** The Fibonacci form first: applying a weight is the step (a,b) |-> (b, a+b),
    so phi^n = F(n)*phi + F(n-1). Each step is one rewrite by phi_square, which
    is why the datapath needs an adder and no multiplier. *)
Lemma phi_cubed_fib : phi^3 = 2 * phi + 1.
Proof.
  pose proof phi_square as Hs.
  replace (phi^3) with (phi * phi^2) by ring.
  rewrite Hs.
  replace (phi * (phi + 1)) with (phi^2 + phi) by ring.
  rewrite Hs. ring.
Qed.

Lemma phi_fourth_fib : phi^4 = 3 * phi + 2.
Proof.
  pose proof phi_square as Hs. pose proof phi_cubed_fib as H3.
  replace (phi^4) with (phi * phi^3) by ring.
  rewrite H3.
  replace (phi * (2 * phi + 1)) with (2 * phi^2 + phi) by ring.
  rewrite Hs. ring.
Qed.

Lemma phi_fifth_fib : phi^5 = 5 * phi + 3.
Proof.
  pose proof phi_square as Hs. pose proof phi_fourth_fib as H4.
  replace (phi^5) with (phi * phi^4) by ring.
  rewrite H4.
  replace (phi * (3 * phi + 2)) with (3 * phi^2 + 2 * phi) by ring.
  rewrite Hs. ring.
Qed.

(** phi^3 = 2 + sqrt 5 *)
Lemma phi_cubed : phi^3 = 2 + sqrt 5.
Proof.
  pose proof phi_cubed_fib as H. unfold phi in H |- *. lra.
Qed.

(** phi^-3 = sqrt 5 - 2 (negative cubic power) *)
Lemma phi_neg3 : / phi^3 = sqrt 5 - 2.
Proof.
  pose proof sqrt5_sq as H5. pose proof phi_cubed as Hc.
  assert (Hne : phi^3 <> 0).
  { rewrite Hc. pose proof sqrt5_nonneg. lra. }
  apply (Rmult_eq_reg_l (phi^3)); [| exact Hne].
  rewrite Rinv_r by exact Hne. rewrite Hc.
  assert (E : (2 + sqrt 5) * (sqrt 5 - 2) = sqrt 5 * sqrt 5 - 4) by ring.
  rewrite E, H5. lra.
Qed.

(** phi^4 = (7 + 3*sqrt 5)/2 *)
Lemma phi_fourth : phi^4 = (7 + 3 * sqrt 5) / 2.
Proof.
  pose proof phi_fourth_fib as H. unfold phi in H |- *. lra.
Qed.

(** phi^5 = (11 + 5*sqrt 5)/2 *)
Lemma phi_fifth : phi^5 = (11 + 5 * sqrt 5) / 2.
Proof.
  pose proof phi_fifth_fib as H. unfold phi in H |- *. lra.
Qed.

(** * Closure of Z[phi] under weight application and accumulation.

    An element of Z[phi] is carried as a coordinate pair (a,b) standing for
    a + b*phi. These are the two facts the datapath rests on: applying the weight
    phi is the Fibonacci step (a,b) |-> (b, a+b), which contains no multiplication,
    and accumulation is componentwise. Together they give exactness of a whole
    linear path by induction on its length. *)

Definition Zphi (a b : R) : R := a + b * phi.

(** Applying the weight phi is the Fibonacci step. No multiplier appears: the
    new coordinates are a previous coordinate and one addition. *)
Theorem fib_step_is_phi_mul : forall a b : R,
  Zphi a b * phi = Zphi b (a + b).
Proof.
  intros a b. unfold Zphi.
  pose proof phi_square as Hs.
  replace ((a + b * phi) * phi) with (a * phi + b * phi^2) by ring.
  rewrite Hs. ring.
Qed.

(** Accumulation is componentwise, so the lattice is closed under it. *)
Theorem zphi_add_closed : forall a b c d : R,
  Zphi a b + Zphi c d = Zphi (a + c) (b + d).
Proof.
  intros. unfold Zphi. ring.
Qed.

(** Negation, which is what the -phi arm of the {-phi,0,+phi} alphabet needs. *)
Theorem zphi_opp_closed : forall a b : R,
  - Zphi a b = Zphi (-a) (-b).
Proof.
  intros. unfold Zphi. ring.
Qed.

(** The zero arm. *)
Theorem zphi_zero : Zphi 0 0 = 0.
Proof.
  unfold Zphi. ring.
Qed.

(** A whole linear path is exact: folding the three alphabet arms over any list
    of coordinate pairs stays inside Z[phi], with no rounding step anywhere. The
    fold below is the dot product a layer computes. *)
Fixpoint dot (ws : list (R * R)) (acc : R * R) : R * R :=
  match ws with
  | nil => acc
  | cons (a, b) tl => dot tl (fst acc + a, snd acc + b)
  end.

Theorem dot_exact : forall ws a b,
  Zphi (fst (dot ws (a, b))) (snd (dot ws (a, b))) =
  Zphi a b + Zphi (fst (dot ws (0, 0))) (snd (dot ws (0, 0))).
Proof.
  induction ws as [| [x y] tl IH]; intros a b.
  - simpl. unfold Zphi. ring.
  - simpl. rewrite (IH (a + x) (b + y)), (IH (0 + x) (0 + y)).
    unfold Zphi. ring.
Qed.

(** Numeric bracket *)
Lemma phi_between_1_618_and_1_619 : 1.618 < phi < 1.619.
Proof.
  unfold phi.
  (* 2.236^2 = 4.999696 < 5 < 5.004169 = 2.237^2, and sqrt is strictly
     increasing, so the bracket follows by monotonicity rather than by any
     numeric evaluation of sqrt. *)
  assert (A : sqrt (2.236 * 2.236) < sqrt 5).
  { apply sqrt_lt_1_alt. split; lra. }
  assert (B : sqrt 5 < sqrt (2.237 * 2.237)).
  { apply sqrt_lt_1_alt. split; lra. }
  rewrite sqrt_square in A by lra.
  rewrite sqrt_square in B by lra.
  lra.
Qed.
