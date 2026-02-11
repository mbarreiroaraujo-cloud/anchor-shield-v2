use anchor_lang::prelude::*;
use anchor_spl::token::{Token, TokenAccount, Mint};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod safe_program {
    use super::*;

    pub fn initialize_token(ctx: Context<InitToken>) -> Result<()> {
        msg!("Token initialized safely");
        Ok(())
    }
}

/// This struct uses init_if_needed BUT adds explicit constraint checks
/// for delegate and close_authority — the safe mitigation pattern.
#[derive(Accounts)]
pub struct InitToken<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init_if_needed,
        payer = payer,
        token::mint = mint,
        token::authority = authority,
        constraint = token_account.delegate.is_none(),
        constraint = token_account.close_authority.is_none(),
    )]
    pub token_account: Account<'info, TokenAccount>,

    pub mint: Account<'info, Mint>,
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}
