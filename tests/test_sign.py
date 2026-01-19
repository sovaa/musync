"""Tests for musync.sign module."""
import pytest
import musync.sign


def test_ret_default():
    """Test that ret() returns default value."""
    musync.sign.setret(musync.sign.INTERRUPT)
    assert musync.sign.ret() == musync.sign.INTERRUPT


def test_setret():
    """Test setret() function."""
    musync.sign.setret(musync.sign.EXCEPTION)
    assert musync.sign.ret() == musync.sign.EXCEPTION
    musync.sign.setret(musync.sign.INTERRUPT)  # Reset


def test_interrupt_handler():
    """Test interrupt_handler function."""
    musync.sign.Interrupt = False
    musync.sign.interrupt_handler(None)
    assert musync.sign.Interrupt is True
    musync.sign.Interrupt = False  # Reset
