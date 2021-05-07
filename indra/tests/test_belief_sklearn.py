import random
import pickle
import numpy as np
from copy import copy
from collections import defaultdict
from os.path import join, abspath, dirname
from nose.tools import raises
from sklearn.linear_model import LogisticRegression
from indra.sources import signor
from indra.belief import BeliefEngine
from indra.tools import assemble_corpus as ac
from indra.statements import Evidence
from indra.belief.sklearn.wrapper import CountsModel
from indra.belief.sklearn.scorer import SklearnScorer

# A set of test statements derived from SIGNOR only
# (these include many different stmt types)
test_stmt_path = join(dirname(abspath(__file__)),
                      'belief_sklearn_test_stmts.pkl')

# An alternative set of test statements derived from the curated stmt dataset
# (these include supports/supported_by)
test_stmt_cur_path = join(dirname(abspath(__file__)),
                          'belief_sklearn_test_stmts_cur.pkl')

# A statement dataframe sample
test_df_path = join(dirname(abspath(__file__)),
                    'belief_sklearn_test_df.pkl')

with open(test_stmt_path, 'rb') as f:
    test_stmts, y_arr_stmts = pickle.load(f)

with open(test_stmt_cur_path, 'rb') as f:
    test_stmts_cur, y_arr_stmts_cur = pickle.load(f)

with open(test_df_path, 'rb') as f:
    test_df, y_arr_df = pickle.load(f)


# A set of statements derived from Signor used for testing purposes.
def _dump_test_data(filename, num_per_type=10):
    """Get corpus of statements for testing that has a range of stmt types."""
    sp = signor.process_from_web()
    # Group statements by type
    stmts_by_type = defaultdict(list)
    for stmt in sp.statements:
        stmts_by_type[stmt.__class__].append(stmt)
    # Sample statements of each type (without replacement)
    stmt_sample = []
    for stmt_type, stmt_list in stmts_by_type.items():
        if len(stmt_list) <= num_per_type:
            stmt_sample.extend(stmt_list)
        else:
            stmt_sample.extend(random.sample(stmt_list, num_per_type))
    # Make a random binary class vector for the stmt list
    y_arr = [random.choice((0, 1)) for s in stmt_sample]
    with open(test_stmt_path, 'wb') as f:
        pickle.dump((stmt_sample, y_arr), f)
    return stmt_sample


def test_counts_wrapper():
    """Instantiate counts wrapper and make stmt matrix"""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser']
    cw = CountsModel(lr, source_list)


# TODO: Made this so it's not a ValueError, this may change back in the future
#@raises(ValueError)
def test_missing_source():
    """Check that all source_apis in training data are in source list."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser']
    cw = CountsModel(lr, source_list)
    # Should error because test stmts are from signor and signor
    # is not in list
    cw.stmts_to_matrix(test_stmts)


def test_stmts_to_matrix():
    """Check that all source_apis in training data are in source list."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    x_arr = cw.stmts_to_matrix(test_stmts)
    assert isinstance(x_arr, np.ndarray), 'x_arr should be a numpy array'
    assert x_arr.shape == (len(test_stmts), len(source_list)), \
            'stmt matrix dimensions should match test stmts'
    assert set(x_arr.sum(axis=0)) == set([0, 0, len(test_stmts)]), \
           'Signor col should be 1 in every row, other cols 0.'
    # Try again with statement type
    cw = CountsModel(lr, source_list, use_stmt_type=True)
    num_types = len(cw.stmt_type_map)
    x_arr = cw.stmts_to_matrix(test_stmts)
    assert x_arr.shape == (len(test_stmts), len(source_list) + num_types), \
        'matrix should have a col for sources and other cols for every ' \
        'statement type.'


def test_fit_stmts():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    cw.fit(test_stmts, y_arr_stmts)
    # Once the model is fit, the coef_ attribute should be defined
    assert 'coef_' in cw.model.__dict__


def test_fit_stmts_predict_stmts():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    cw.fit(test_stmts, y_arr_stmts)
    probs = cw.predict_proba(test_stmts)
    assert probs.shape == (len(test_stmts), 2), \
        'prediction results should have dimension (# stmts, # classes)'
    log_probs = cw.predict_log_proba(test_stmts)
    assert log_probs.shape == (len(test_stmts), 2), \
        'prediction results should have dimension (# stmts, # classes)'
    preds = cw.predict(test_stmts)
    assert preds.shape == (len(test_stmts),), \
        'prediction results should have dimension (# stmts)'


@raises(ValueError)
def test_check_df_cols_err():
    """Drop a required column and make sure we get a ValueError."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    cw.df_to_matrix(test_df.drop('agB_ns', axis=1))


def test_check_df_cols_noerr():
    """Test dataframe should not raise ValueError."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    cw.df_to_matrix(test_df)


def test_df_to_matrix():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    x_arr = cw.df_to_matrix(test_df)
    assert isinstance(x_arr, np.ndarray), 'x_arr should be a numpy array'
    assert x_arr.shape == (len(test_df), len(source_list)), \
            'stmt matrix dimensions should match test stmts'
    assert x_arr.shape == (len(test_df), len(source_list))
    # Try again with statement type
    cw = CountsModel(lr, source_list, use_stmt_type=True)
    num_types = len(cw.stmt_type_map)
    x_arr = cw.df_to_matrix(test_df)
    assert x_arr.shape == (len(test_df), len(source_list) + num_types), \
        'matrix should have a col for sources and other cols for every ' \
        'statement type.'


def test_fit_df():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'medscan', 'trips', 'rlimsp']
    cw = CountsModel(lr, source_list)
    cw.fit(test_df, y_arr_df)
    # Once the model is fit, the coef_ attribute should be defined
    assert 'coef_' in cw.model.__dict__


def test_fit_stmts_pred_df():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    # Train on statement data
    cw.fit(test_stmts, y_arr_stmts)
    # Predict on DF data
    probs = cw.predict_proba(test_df)
    assert probs.shape == (len(test_df), 2), \
        'prediction results should have dimension (# stmts, # classes)'
    log_probs = cw.predict_log_proba(test_df)
    assert log_probs.shape == (len(test_df), 2), \
        'prediction results should have dimension (# stmts, # classes)'
    preds = cw.predict(test_df)
    assert preds.shape == (len(test_df),), \
        'prediction results should have dimension (# stmts)'


def test_fit_df_pred_stmts():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    # Train on statement data
    cw.fit(test_df, y_arr_df)
    # Predict on DF data
    probs = cw.predict_proba(test_stmts)
    assert probs.shape == (len(test_stmts), 2), \
        'prediction results should have dimension (# stmts, # classes)'
    log_probs = cw.predict_log_proba(test_stmts)
    assert log_probs.shape == (len(test_stmts), 2), \
        'prediction results should have dimension (# stmts, # classes)'
    preds = cw.predict(test_stmts)
    assert preds.shape == (len(test_stmts),), \
        'prediction results should have dimension (# stmts)'


@raises(ValueError)
def test_check_missing_source_counts():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser']
    cw = CountsModel(lr, source_list)
    # Drop the source_counts column
    df_no_sc = test_df.drop('source_counts', axis=1)
    # Should error
    cw.fit(df_no_sc, y_arr_df)


def test_check_source_columns():
    lr = LogisticRegression()
    source_list = ['reach', 'sparser']
    cw = CountsModel(lr, source_list)
    # Drop the source_counts column
    df_sc = test_df.drop('source_counts', axis=1)
    # Add reach and sparser columns
    df_sc['reach'] = 0
    df_sc['sparser'] = 0
    # Should not error
    cw.fit(df_sc, y_arr_df)


def test_matrix_to_matrix():
    """Check that we get a matrix back when passed to to_matrix."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    # Train on statement data
    stmt_arr = cw.to_matrix(test_df)
    assert cw.to_matrix(stmt_arr) is stmt_arr, \
            'If passed a numpy array to_matrix should return it back.'


@raises(ValueError)
def test_use_members_with_df():
    """Check that we can't set use_num_members when passing a DataFrame."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list, use_num_members=True)
    # This should error because stmt DataFrame doesn't contain num_members
    # info
    stmt_arr = cw.to_matrix(test_df)


def test_use_members_with_stmts():
    """Check that we can set use_num_members when passing statements."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list, use_num_members=True)
    x_arr = cw.to_matrix(test_stmts)
    assert x_arr.shape == (len(test_stmts), len(source_list)+1), \
            'stmt matrix dimensions should match test stmts plus num_members'


def setup_belief():
    # Make a model
    lr = LogisticRegression()
    # Get all the sources
    source_list = CountsModel.get_all_sources(test_stmts_cur)
    cw = CountsModel(lr, source_list)
    # Train on curated stmt data
    cw.fit(test_stmts_cur, y_arr_stmts_cur)
    # Run predictions on test statements
    probs = cw.predict_proba(test_stmts_cur)[:, 1]
    # Now check if we get these same beliefs set on the statements when we
    # run with the belief engine:
    # Get scorer and belief engine instances for trained model
    skls = SklearnScorer(cw)
    be = BeliefEngine(scorer=skls)
    # Make a shallow copy of the test stmts so that we don't change beliefs
    # of the global instances as a side-effect of this test
    test_stmts_copy = copy(test_stmts_cur)
    return be, test_stmts_copy, probs


def test_set_prior_probs():
    # Get probs for a set of statements, and a belief engine instance
    be, test_stmts_copy, probs = setup_belief()
    # Set beliefs
    be.set_prior_probs(test_stmts_copy)
    beliefs = [s.belief for s in test_stmts_copy]
    # Check that they match
    assert np.allclose(beliefs, probs), \
           "Statement beliefs should be set to predicted probabilities."


@raises(ValueError)
def test_df_extra_ev_value_error():
    """to_matrix should raise ValueError if given a DataFrame and extra
       evidence (for now)."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    cw.to_matrix(test_df, extra_evidence=[[5]])


@raises(ValueError)
def test_extra_evidence_length():
    """Should raise ValueError because the extra_evidence list is not the
    same length as the list of statements."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    extra_ev = [[5]]
    x_arr = cw.stmts_to_matrix(test_stmts, extra_evidence=extra_ev)


@raises(ValueError)
def test_extra_evidence_content():
    """Should raise ValueError if extra_evidence list entries are not
    Evidence objects or empty lists."""
    lr = LogisticRegression()
    source_list = ['reach', 'sparser', 'signor']
    cw = CountsModel(lr, source_list)
    extra_ev = ([[5]] * (len(test_stmts) - 1)) + [[]]
    x_arr = cw.stmts_to_matrix(test_stmts, extra_evidence=extra_ev)


def test_set_hierarchy_probs():
    # Get probs for a set of statements, and a belief engine instance
    be, test_stmts_copy, prior_probs = setup_belief()
    # Set beliefs on the flattened statements
    top_level = ac.filter_top_level(test_stmts_copy)
    be.set_hierarchy_probs(test_stmts_copy)
    # Compare hierarchy probs to prior probs
    for stmt, prior_prob in zip(test_stmts_copy, prior_probs):
        # Check that the top-level statements beliefs have not changed
        if stmt in top_level:
            assert stmt.belief == prior_prob
        # Presumably the hierarchy probabilities should always be greater
        # than the prior probs
        else:
            if stmt.belief != prior_prob:
                print(stmt, prior_prob, stmt.belief)
                assert stmt.belief >= prior_prob

# Refactor BeliefScorer and SimpleScorer to support score_statements

# Add docstrings and type hints to all functions

# To separate scorer from wrapper? Or combine?

# build_refinements_graph now takes a list of statements rather than a list
# of statements by hash. However, the structure of the graph itself is the
# same, so any code that extends or otherwise uses the graph will still work.

# Implement model training via belief engine to allow collection of
# supp/supp_by evidence? (raises question of whether the supp/supp_by
# statements will have been curated as well

# Note that 1) statements that are explicitly in the list will not have
# beliefs estimated and 2) calling set_hierarchy_probs a second time
# with a different set of statements will cause error from the re-used
# refinements graph

# Set linked_probs seems wacky--shouldn't be an instance method. Maybe make
# a staticmethod?

# Negated evidence excluded in get_refinement_probs but is actually factored
# in 

# Refactor BE tools to be able to collect extra evidence for statements
# outside of the belief engine hierarchy_probs, by using build_refinements
# _graph and get_hierarchy_probs, etc.

if __name__ == '__main__':
    test_set_hierarchy_probs()
