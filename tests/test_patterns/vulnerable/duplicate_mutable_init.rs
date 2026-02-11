use anchor_lang::prelude::*;
use anchor_spl::token::{Token, TokenAccount, Mint};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod vulnerable_program {
    use super::*;

    pub fn transfer_with_init(ctx: Context<TransferWithInit>) -> Result<()> {
        // Both source and dest could be the same account
        msg!("Transfer completed");
        Ok(())
    }
}

#[derive(Accounts)]
pub struct TransferWithInit<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init_if_needed,
        payer = payer,
        token::mint = mint,
        token::authority = authority,
    )]
    pub destination: Account<'info, TokenAccount>,

    #[account(mut)]
    pub source: Account<'info, TokenAccount>,

    pub mint: Account<'info, Mint>,
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}
